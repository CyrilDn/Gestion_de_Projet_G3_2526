from src.materiel.capteurs.CapteurUltrason import CapteurUltrason
import unittest
from unittest.mock import MagicMock

class TestCapteurUltrason(unittest.TestCase):
    def setUp(self):
        self.capteur = CapteurUltrason(pin_trigger=1, pin_echo=2, lib_gpio=None)

    def test_initialisation(self):
        self.assertEqual(self.capteur.pin_trigger, 1)
        self.assertEqual(self.capteur.pin_echo, 2)
        self.assertEqual(self.capteur.timeout, 0.02)

    def test_mesurer_distance(self):
        faux_gpio = MagicMock()
        capteur = CapteurUltrason(pin_trigger=1, pin_echo=2, lib_gpio=faux_gpio)
        distance_test = capteur.mesurer_distance(200e-6)  # 200µs
        self.assertIsNotNone(distance_test)

    # ========== TESTS DE DÉLAIS ==========

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

    def test_timeout_distance_trop_grande(self):
        """Cas limite: durée > 30ms => timeout"""
        with self.assertRaises(TimeoutError):
            self.capteur.mesurer_distance(0.04)  # 40ms (dépasse le timeout)

    # ========== TESTS MOYENNAGE ==========
    
    def test_moyennage_deux_mesures(self):
        """Moyennage de deux mesures successives"""
        distance1 = self.capteur.mesurer_distance(200e-6)  # ~3.43 cm
        distance2 = self.capteur.mesurer_distance(200e-6)  # ~3.43 cm
        
        moyenne = (distance1 + distance2) / 2
        self.assertAlmostEqual(moyenne, 3.43, places=2)
    
    def test_moyennage_plusieurs_mesures(self):
        """Moyennage de plusieurs mesures successives"""
        pulse_durations = [100e-6, 150e-6, 200e-6, 250e-6, 300e-6]
        distances = [self.capteur.mesurer_distance(pd) for pd in pulse_durations]
        
        moyenne = sum(distances) / len(distances)
        self.assertGreater(moyenne, 0)
        self.assertIsNotNone(moyenne)
    
    def test_moyennage_avec_bruit(self):
        """Moyennage avec variation brutale (bruit)"""
        # Mesures normales: ~3.43 cm
        distances_normales = [self.capteur.mesurer_distance(200e-6) for i in range(3)]
        
        # Mesure aberrante (bruit): ~8.58 cm
        distance_bruit = self.capteur.mesurer_distance(500e-6)
        
        # Mesures normales après le bruit
        distances_apres = [self.capteur.mesurer_distance(200e-6) for i in range(3)]
        
        # Vérifier que les mesures normales sont similaires
        moyenne_avant = sum(distances_normales) / len(distances_normales)
        moyenne_apres = sum(distances_apres) / len(distances_apres)
        
        self.assertAlmostEqual(moyenne_avant, moyenne_apres, places=1)
        self.assertGreater(abs(distance_bruit - moyenne_avant), 2)  # Bruit clairement détectable

    # ========== TESTS BRUIT ==========

    def test_bruit_variation_brutale(self):
        """Test de détection de bruit avec variation brutale"""
        distance_normale = self.capteur.mesurer_distance(200e-6)  # ~3.43 cm
        distance_bruit = self.capteur.mesurer_distance(500e-6)  # ~8.58 cm
        
        variation = abs(distance_bruit - distance_normale) / distance_normale
        self.assertGreater(variation, CapteurUltrason.SEUIL_VARIATION_BRUIT)
        print(f"Variation détectée: {variation:.2f} (bruit détecté)")

        


if __name__ == '__main__':
    unittest.main() 