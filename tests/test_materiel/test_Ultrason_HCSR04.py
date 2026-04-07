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
        distance_test = capteur.mesurer_distance(200e-6)  # 200µs
        self.assertIsNotNone(distance_test)

    def test_distance_trop_faible_moins_100us(self):
        """Cas limite: durée < 100µs => distance trop faible"""
        with self.assertRaises(ValueError):
            self.capteur.mesurer_distance(50e-6)
    
    def test_distance_valide_a_100us(self):
        """Test à la limite minimale: 100µs => distance acceptable"""
        distance = self.capteur.mesurer_distance(100e-6)  # Exactement 100µs
        self.assertIsNotNone(distance)
    
    def test_distance_normale(self):
        """Test avec une durée normale: 200µs"""
        distance = self.capteur.mesurer_distance(200e-6)  # 200µs
        # Vérifier avec une approximation (3.43 cm)
        self.assertAlmostEqual(distance, 3.43, places=2)

    # ========== TESTS BRUIT/ÉCHO MULTIPLE ==========
    
    def test_bruit_variation_brusque_superieure_20_pourcent(self):
        """Variation brusque > 20% => bruit/écho multiple détecté"""
        # Première mesure: 30 cm
        est_bruit_1 = self.capteur.est_bruit_ou_echo_multiple(30.0)
        self.assertFalse(est_bruit_1, "Première mesure ne peut pas être du bruit")
        
        # Deuxième mesure: 30 * 1.25 = 37.5 cm (+25% de variation)
        est_bruit_2 = self.capteur.est_bruit_ou_echo_multiple(37.5)
        self.assertTrue(est_bruit_2, "Variation de +25% devrait être détectée comme bruit")
    
    def test_variation_acceptable_moins_20_pourcent(self):
        """Variation < 20% => pas du bruit"""
        # Première mesure: 30 cm
        est_bruit_1 = self.capteur.est_bruit_ou_echo_multiple(30.0)
        self.assertFalse(est_bruit_1)
        
        # Deuxième mesure: 30 * 1.10 = 33 cm (+10% de variation)
        est_bruit_2 = self.capteur.est_bruit_ou_echo_multiple(33.0)
        self.assertFalse(est_bruit_2, "Variation de +10% ne devrait pas être du bruit")
    
    def test_bruit_variation_negative_brusque(self):
        """Variation négative brusque > 20% => bruit/écho multiple détecté"""
        # Première mesure: 50 cm
        est_bruit_1 = self.capteur.est_bruit_ou_echo_multiple(50.0)
        self.assertFalse(est_bruit_1)
        
        # Deuxième mesure: 50 * 0.75 = 37.5 cm (-25% de variation)
        est_bruit_2 = self.capteur.est_bruit_ou_echo_multiple(37.5)
        self.assertTrue(est_bruit_2, "Variation de -25% devrait être détectée comme bruit")
    
    def test_bruit_variation_limite_20_pourcent(self):
        """Variation exactement à 20% => seuil limite"""
        # Première mesure: 100 cm
        self.capteur.est_bruit_ou_echo_multiple(100.0)
        
        # Deuxième mesure: 100 * 1.20 = 120 cm (exactement 20%)
        est_bruit = self.capteur.est_bruit_ou_echo_multiple(120.0)
        self.assertFalse(est_bruit, "Variation exactement 20% ne devrait pas dépasser le seuil")
    
    def test_sequence_mesures_avec_bruit(self):
        """Séquence de mesures avec détection du bruit"""
        # Mesure 1: 25.0 cm (référence)
        est_bruit_1 = self.capteur.est_bruit_ou_echo_multiple(25.0)
        self.assertFalse(est_bruit_1)
        
        # Mesure 2: 25.5 cm (+2% - normal)
        est_bruit_2 = self.capteur.est_bruit_ou_echo_multiple(25.5)
        self.assertFalse(est_bruit_2, "Petite variation acceptable")
        
        # Mesure 3: 31.0 cm (+21% - bruit!)
        est_bruit_3 = self.capteur.est_bruit_ou_echo_multiple(31.0)
        self.assertTrue(est_bruit_3, "Grande variation = bruit détecté")
        
        # Mesure 4: 31.2 cm (nouvelle référence après bruit)
        est_bruit_4 = self.capteur.est_bruit_ou_echo_multiple(31.2)
        self.assertFalse(est_bruit_4, "Petite variation après le bruit")


if __name__ == '__main__':
    unittest.main() 