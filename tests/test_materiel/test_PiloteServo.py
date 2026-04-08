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
        # On positionne à 90 une première fois
        self.direction.positionner(90)
        # On réinitialise le compteur d'appels du mock
        self.direction.servo_moteur.reset_mock()

        # On demande à nouveau 90
        resultat = self.direction.positionner(90)

        # L'action doit réussir (True), mais le moteur physique ne doit pas être sollicité à nouveau
        self.assertTrue(resultat)
        # Vérifie que la propriété 'angle' du mock n'a pas été modifiée une 2ème fois
        self.direction.servo_moteur.assert_not_called()

    def test_reaction_securite_perte_signal(self):
        """Teste la réaction si la puce PCA9685 est débranchée ou plante (Erreur I2C)."""

        # 1. On crée un "Stub" (un faux objet) très simple qui lève une erreur
        # dès qu'on essaie de modifier son angle.
        class FauxServoEnPanne:
            @property
            def angle(self):
                return 90  # Valeur factice pour la lecture

            @angle.setter
            def angle(self, valeur):
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
        self.direction.en_erreur = True
        self.direction.servo_moteur.reset_mock()

        resultat = self.direction.positionner(90)

        self.assertFalse(resultat)
        # Le contrôleur ne doit même pas tenter de communiquer avec le composant physique
        self.direction.servo_moteur.assert_not_called()


if __name__ == "__main__":
    unittest.main()
