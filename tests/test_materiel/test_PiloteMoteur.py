from src.materiel.actionneurs.PiloteMoteur_L298N import PiloteMoteur_L298N

import unittest
from unittest.mock import MagicMock, patch, Mock


class TestPiloteMoteur_L298N(unittest.TestCase):
    def setUp(self):
        """Initialiser le moteur avec un GPIO simulé"""
        self.faux_gpio = MagicMock()
        self.faux_pwm = MagicMock()
        self.faux_gpio.PWM = MagicMock(return_value=self.faux_pwm)
        
        self.moteur = PiloteMoteur_L298N(pin_in1=17, pin_in2=27, pin_pwm=22, lib_gpio=self.faux_gpio)

    # ========== TESTS SEUIL PWM MINIMAL 30% ==========

    def test_pwm_inferieur_seuil_minimal_leve_erreur(self):
        """PWM < 30% lève ValueError"""
        with self.assertRaises(ValueError):
            self.moteur.avancer(vitesse=20)
            ValueError("Vitesse doit être supérieure ou égale à 30% pour avancer")
    
    def test_pwm_zero_accepte(self):
        """PWM = 0% est accepté (arrêt)"""
        self.moteur.arreter()
        self.assertEqual(self.moteur.pwm_applique, 0)
    
    def test_pwm_exactement_seuil_accepte(self):
        """PWM = 30% exactement (seuil) est accepté"""
        self.moteur.avancer(vitesse=30)
        self.assertEqual(self.moteur.pwm_applique, 30)
    
    def test_pwm_normal_accepte(self):
        """PWM = 100% (normal) est accepté"""
        self.moteur.avancer(vitesse=100)
        self.assertEqual(self.moteur.pwm_applique, 100)
    
    def test_reculer_pwm_inferieur_seuil_leve_erreur(self):
        """Reculer avec PWM < seuil lève ValueError"""
        with self.assertRaises(ValueError):
            self.moteur.reculer(vitesse=15)
            ValueError("Vitesse doit être supérieure ou égale à 30% pour reculer")
  