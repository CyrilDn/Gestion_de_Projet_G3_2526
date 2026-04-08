import unittest
from unittest.mock import MagicMock

from src.materiel.capteurs.DetecteurLigneArrivee_IR import DetecteurLigneArrivee


class TestDetecteurLigneArrivee(unittest.TestCase):
    def setUp(self):
        """
        Cette méthode s'exécute avant chaque test.
        Elle prépare notre environnement simulé.
        """
        # 1. Création d'une fausse bibliothèque GPIO
        self.mock_gpio = MagicMock()

        # 2. Simulation de la constante "IN" de la vraie librairie RPi.GPIO
        self.mock_gpio.IN = "ENTREE_SIMULEE"

        # 3. Choix d'un pin arbitraire pour le test
        self.pin_test = 14

        # 4. Instanciation de notre objet avec le faux GPIO
        self.detecteur = DetecteurLigneArrivee(self.pin_test, self.mock_gpio)

    def test_initialisation_configure_pin_en_entree(self):
        """Vérifie que __init__ appelle bien gpio.setup() avec les bons arguments."""
        self.mock_gpio.setup.assert_called_once_with(self.pin_test, self.mock_gpio.IN)

    def test_est_sur_ligne_arrivee_quand_detectee(self):
        """Vérifie le comportement si le capteur indique la présence de la ligne."""
        # On simule que la méthode input() renvoie 1 (ou True)
        self.mock_gpio.input.return_value = 1

        resultat = self.detecteur.est_sur_ligne_arrivee()

        # On s'attend à ce que le résultat soit True
        self.assertTrue(resultat)
        # On vérifie que la lecture a bien été faite sur le bon pin
        self.mock_gpio.input.assert_called_once_with(self.pin_test)

    def test_n_est_pas_sur_ligne_arrivee(self):
        """Vérifie le comportement si le capteur n'indique rien (sol classique)."""
        # On simule que la méthode input() renvoie 0 (ou False)
        self.mock_gpio.input.return_value = 0

        resultat = self.detecteur.est_sur_ligne_arrivee()

        # On s'attend à ce que le résultat soit False
        self.assertFalse(resultat)
        self.mock_gpio.input.assert_called_once_with(self.pin_test)


if __name__ == "__main__":
    unittest.main()
