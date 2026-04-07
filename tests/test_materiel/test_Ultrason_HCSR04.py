from src.materiel.capteurs.CapteurUltrason import CapteurUltrason
import unittest
from unittest.mock import MagicMock

class TestCapteurUltrason(unittest.TestCase):
    def setUp(self):
        self.capteur = CapteurUltrason(pin_trigger=1, pin_echo=2)

    def test_initialisation(self):
        self.assertEqual(self.capteur.pin_trigger, 1)
        self.assertEqual(self.capteur.pin_echo, 2)
        self.assertEqual(self.capteur.timeout, 0.02)

    def test_mesurer_distance(self):
        faux_gpio = MagicMock()
        capteur = CapteurUltrason(pin_trigger=1, pin_echo=2, lib_gpio=faux_gpio)
        distance_test = capteur.mesurer_distance()
        self.assertEqual(distance_test, None)  # En l'absence de logique de mesure, on s'attend à None



if __name__ == '__main__':
    unittest.main() 