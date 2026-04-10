import unittest
from unittest.mock import MagicMock, patch
import sys

# Simulation complète de l'environnement matériel Adafruit et I2C
sys.modules["board"] = MagicMock()  # Carte physique (GPIO, ...)
sys.modules["busio"] = (
    MagicMock()
)  # Gere les communications materielles (I2C, UART, SPI, ...)
sys.modules["adafruit_pca9685"] = MagicMock()  # Gere le PWM driver (PCA9685)
sys.modules["adafruit_motor"] = (
    MagicMock()
)  # Traduit les instructions humaines en signal PWM

from src.materiel.actionneurs.PiloteServo_PCA9685 import ServoDirectionPCA


class FauxServo:
    def __init__(self):
        self.nombre_changement_angle = 0
        self.__angle = 60

    @property
    def angle(self):
        return self.__angle

    @angle.setter
    def angle(self, val):
        self.nombre_changement_angle += 1
        self.__angle = val


class TestServoDirectionPCA(unittest.TestCase):
    def setUp(self):
        # On initialise un servo virtuel sur le canal 0, limité entre 45 et 135
        self.direction = ServoDirectionPCA(canal=0, angle_min=45, angle_max=135)

    def test_arrondi_et_cast(self):
        """Teste le cast propre et l'arrondi des valeurs avant l'envoi."""
        # Un float doit être arrondi à l'entier le plus proche
        self.assertEqual(self.direction.formater_angle(90.1), 90)
        self.assertEqual(self.direction.formater_angle(90.6), 91)

        # Une chaîne de caractères contenant un nombre doit être convertie
        self.assertEqual(self.direction.formater_angle("45"), 45)
        self.assertEqual(self.direction.formater_angle("45.8"), 46)

        # Une valeur non numérique doit être interceptée (renvoie 90 par défaut ici)
        self.assertEqual(self.direction.formater_angle("gauche"), 90)

    def test_limites_angles(self):
        """Teste que les valeurs hors limites sont corrigées et restreintes."""
        # Valeur négative -> bloquée au minimum (45)
        self.assertEqual(self.direction.formater_angle(-15), 45)

        # Valeur excessive -> bloquée au maximum (135)
        self.assertEqual(self.direction.formater_angle(250), 135)

        # Cas d'un bug d'algorithme envoyant "l'infini"
        self.assertEqual(self.direction.formater_angle(float("inf")), 90)

    def test_stabilite_commandes_repetitives(self):
        """Teste qu'une commande identique n'est pas renvoyée au contrôleur (sauvegarde du bus I2C)."""

        self.direction.servo_moteur = FauxServo()

        # première mise a 90 doit changer l'angle
        self.direction.positionner(90)
        self.assertEqual(self.direction.servo_moteur.angle, 90)
        self.assertEqual(self.direction.servo_moteur.nombre_changement_angle, 1)

        # comme l'angle etait deja a 90, il ne doit pas se mettre a jour. `nombre_changement_angle` est toujours a 1
        resultat = self.direction.positionner(90)
        self.assertTrue(resultat)
        self.assertEqual(self.direction.servo_moteur.nombre_changement_angle, 1)

        # nouvel angle => `nombre_changement_angle` est incremente et angle est a jour
        self.direction.positionner(100)
        self.assertEqual(self.direction.servo_moteur.angle, 100)
        self.assertEqual(self.direction.servo_moteur.nombre_changement_angle, 2)

    def test_reaction_securite_perte_signal(self):
        """Teste la réaction si la puce PCA9685 est débranchée ou plante (Erreur I2C)."""

        # 1. On crée un "Stub" (un faux objet) très simple qui lève une erreur
        # dès qu'on essaie de modifier son angle.
        class FauxServoEnPanne:
            def __init__(self):
                self.__angle = 90
                self.nombre_changement_angle = 0

            @property
            def angle(self):
                return self.__angle  # Valeur factice pour la lecture

            @angle.setter
            def angle(self, valeur):
                self.nombre_changement_angle += 1
                # C'est ici qu'on simule la panne physique !
                raise OSError("Bus I2C injoignable")

        # 2. On remplace le mock du pilote par notre faux composant en panne
        self.direction.servo_moteur = FauxServoEnPanne()

        # 3. On tente d'envoyer une commande via notre fonction principale
        resultat = self.direction.positionner(45)

        # 4. On vérifie nos attentes
        self.assertFalse(resultat)
        self.assertTrue(self.direction.en_erreur)

    def test_blocage_apres_erreur_critique(self):
        """Teste qu'aucune commande n'est envoyée si le système est déjà en erreur."""

        # On remplace le composant par notre mock
        self.direction.servo_moteur = FauxServo()

        # 2. On simule l'état d'erreur
        self.direction.en_erreur = True

        # 3. On tente de positionner le servo
        resultat = self.direction.positionner(90)

        # 4. Vérifications
        self.assertFalse(resultat)  # L'action doit être refusée

        # Le compteur doit être resté à 0, prouvant que la propriété .angle n'a jamais été touchée
        self.assertEqual(self.direction.servo_moteur.nombre_changement_angle, 0)


if __name__ == "__main__":
    unittest.main()
