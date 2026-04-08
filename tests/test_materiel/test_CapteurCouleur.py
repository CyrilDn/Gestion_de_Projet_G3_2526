import os
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.materiel.capteurs.CapteurCouleur import CapteurCouleur

class TestCapteurCouleurImports(unittest.TestCase):
    def test_initialiser_avec_busio_et_adafruit_simules(self):
        fake_board = MagicMock()
        fake_board.I2C = MagicMock(return_value="bus-i2c")

        fake_adafruit = MagicMock()
        fake_sensor = MagicMock()
        fake_adafruit.TCS34725 = MagicMock(return_value=fake_sensor)

        with patch.dict(sys.modules, {"board": fake_board, "adafruit_tcs34725": fake_adafruit}):
            capteur = CapteurCouleur("0x29")
            sensor = capteur.initialiser()

        self.assertIs(sensor, fake_sensor)
        fake_board.I2C.assert_called_once()
        fake_adafruit.TCS34725.assert_called_once_with("bus-i2c")


    def test_initialiser_avec_bus_i2c_existant(self):
        fake_adafruit = MagicMock()
        fake_sensor = MagicMock()
        fake_adafruit.TCS34725 = MagicMock(return_value=fake_sensor)

        with patch.dict(sys.modules, {"adafruit_tcs34725": fake_adafruit}):
            capteur = CapteurCouleur("0x29", bus_i2c="bus-i2c")
            sensor = capteur.initialiser()

        self.assertIs(sensor, fake_sensor)
        fake_adafruit.TCS34725.assert_called_once_with("bus-i2c")


    def test_initialiser_sans_adafruit(self):
        fake_busio = MagicMock()
        fake_busio.I2C = MagicMock(return_value="bus-i2c")

        with patch.dict(sys.modules, {"busio": fake_busio}):
            capteur = CapteurCouleur("0x29")
            with self.assertRaises(ImportError):
                capteur.initialiser()

class TestCapteurCouleurLireValeursBrutes(unittest.TestCase):
    def test_lire_valeurs_brutes_depuis_capteur_simule(self):
        capteur = CapteurCouleur("0x29")
        capteur.sensor = MagicMock(color_rgb_bytes=(15, 30, 45), clear=120)

        valeurs = capteur.lire_valeurs_brutes()
        self.assertEqual(valeurs, (15, 30, 45, 120))
    

    def test_lire_valeurs_brutes_depuis_color_raw_si_clear_absent(self):
        sensor = MagicMock(color_rgb_bytes=(5, 10, 15), clear=None, color_raw=(5, 10, 15, 80))
        capteur = CapteurCouleur("0x29")
        capteur.sensor = sensor

        valeurs = capteur.lire_valeurs_brutes()
        self.assertEqual(valeurs, (5, 10, 15, 80))

class TestCapteurCouleurNormaliserRgb(unittest.TestCase):
    def test_normaliser_rgb_avec_valeurs_claires(self):
        capteur = CapteurCouleur("0x29")
        self.assertEqual(capteur.normaliser_rgb(10, 20, 30, 60), (42, 85, 128))

    def test_normaliser_rgb_canal_clair_zero(self):
        capteur = CapteurCouleur("0x29")
        self.assertEqual(capteur.normaliser_rgb(10, 20, 30, 0), (0, 0, 0))

class TestCapteurCouleurDetecterCouleurDominante(unittest.TestCase):
    def setUp(self):
        self.capteur = CapteurCouleur("0x29")

    def test_detecter_couleur_rouge(self):
        self.assertEqual(self.capteur.detecter_couleur_dominante(100, 50, 20, 200), "rouge")

    def test_detecter_couleur_vert(self):
        self.assertEqual(self.capteur.detecter_couleur_dominante(20, 100, 30, 200), "vert")

    def test_detecter_couleur_bleu(self):
        self.assertEqual(self.capteur.detecter_couleur_dominante(10, 20, 100, 200), "bleu")

    def test_detecter_couleur_aucune(self):
        self.assertEqual(self.capteur.detecter_couleur_dominante(0, 0, 0, 0), "aucune")

    def test_detecter_couleur_trop_faible(self):
        self.assertEqual(self.capteur.detecter_couleur_dominante(1, 2, 3, 100), "trop_faible")

    def test_detecter_couleur_saturation(self):
        self.assertEqual(self.capteur.detecter_couleur_dominante(100, 120, 140, 70000), "saturation")


if __name__ == '__main__':
    unittest.main(verbosity=2)