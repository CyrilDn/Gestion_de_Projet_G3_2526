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
        with self.assertRaises(ValueError) as context:
            self.moteur.avancer(vitesse=20)
        self.assertEqual(str(context.exception), "PWM 20% inférieur au seuil minimal 30%")

    def test_pwm_zero_accepte(self):
        """PWM = 0% est accepté (arrêt)"""
        self.moteur.arreter()
        self.assertEqual(self.moteur.pwm_applique, 0)
        self.faux_gpio.output.assert_called_with(self.moteur.pin_in2, False)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(0)
    
    def test_pwm_exactement_seuil_accepte(self):
        """PWM = 30% exactement (seuil) est accepté"""
        self.moteur.avancer(vitesse=30)
        self.assertEqual(self.moteur.pwm_applique, 30)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in1, True)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in2, False)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(30)
    
    def test_pwm_normal_accepte(self):
        """PWM = 100% (normal) est accepté"""
        self.moteur.avancer(vitesse=100)
        self.assertEqual(self.moteur.pwm_applique, 100)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in1, True)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in2, False)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(100)
    
    def test_reculer_pwm_inferieur_seuil_leve_erreur(self):
        """Reculer avec PWM < seuil lève ValueError"""
        with self.assertRaises(ValueError) as context:
            self.moteur.reculer(vitesse=15)
        self.assertEqual(str(context.exception), "PWM 15% inférieur au seuil minimal 30%")

    # ========== TESTS INVERSION DE DIRECTION ==========
    @patch('time.sleep', return_value=None)  # Simuler time.sleep pour éviter les délais réels
    def test_inversion_avancer_reculer_avec_pwm_non_zero(self, mock_sleep):
        """Inversion de direction avec PWM non zéro applique un délai de sécurité"""
        # Avancer à 50%
        self.moteur.avancer(vitesse=50)
        self.assertEqual(self.moteur.direction_actuelle, "avancer")
        self.assertEqual(self.moteur.pwm_applique, 50)
        
        # Vérifier les appels GPIO pour avancer
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in1, True)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in2, False)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(50)

        # Reculer à 50% (inversion de direction)
        self.faux_gpio.reset_mock()
        self.faux_pwm.reset_mock()
        
        self.moteur.reculer(vitesse=50)
        self.assertEqual(self.moteur.direction_actuelle, "reculer")
        self.assertEqual(self.moteur.pwm_applique, 50)
        
        # Vérifier que time.sleep a été appelé avec le délai d'inversion
        mock_sleep.assert_called_with(self.moteur.DELAI_INVERSION)
        
        # Vérifier les appels GPIO pour reculer
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in1, False)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in2, True)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(50)
  
    # ========== TESTS BLOQUAGE ==========
    def test_bloquer_si_pwm_applique_eleve_et_vitesse_zero(self):
        """Moteur bloqué si PWM > 50% et vitesse réelle = 0%"""
        # Simuler un moteur bloqué
        self.moteur.pwm_applique = 60  # PWM élevé
        self.moteur.vitesse = 0  # Vitesse réelle = 0%
        
        est_bloque = self.moteur._verifier_blocage()
        self.assertTrue(est_bloque, "Le moteur devrait être détecté comme bloqué")

    # ========== TESTS RAMPING TRUE DANS AVANCER/RECULER ==========
    @patch('time.sleep', return_value=None)
    def test_avancer_avec_ramping_true(self, mock_sleep):
        """Test avancer() avec ramping=True active le démarrage progressif"""
        with patch.object(self.moteur, '_ramping_progressif') as mock_ramping:
            self.moteur.avancer(vitesse=100, ramping=True)
            
            mock_ramping.assert_called_once()
            call_args = mock_ramping.call_args
            self.assertEqual(call_args[0][0], self.moteur.pwm_applique)  
            self.assertEqual(call_args[0][1], 100)
            self.assertEqual(call_args[0][2], "avancer")

    @patch('time.sleep', return_value=None)
    def test_reculer_avec_ramping_true(self, mock_sleep):
        """Test reculer() avec ramping=True active le démarrage progressif"""
        with patch.object(self.moteur, '_ramping_progressif') as mock_ramping:
            self.moteur.reculer(vitesse=80, ramping=True)
            
            mock_ramping.assert_called_once()
            call_args = mock_ramping.call_args
            self.assertEqual(call_args[0][0], self.moteur.pwm_applique)
            self.assertEqual(call_args[0][1], 80)
            self.assertEqual(call_args[0][2], "reculer")

    @patch('time.sleep', return_value=None)
    def test_avancer_sans_ramping_pas_de_ramping(self, mock_sleep):
        """Test avancer() avec ramping=False ne fait pas de démarrage progressif"""
        with patch.object(self.moteur, '_ramping_progressif') as mock_ramping:
            self.moteur.avancer(vitesse=100, ramping=False)
            
            mock_ramping.assert_not_called()
            self.assertEqual(self.moteur.pwm_applique, 100)
            self.assertEqual(self.moteur.direction_actuelle, "avancer")

    # ========== TESTS CHANGEMENT DE VITESSE ==========
    def test_changer_vitesse_sans_changer_direction(self):
        """Test que changer_vitesse modifie uniquement le PWM"""
        self.moteur.avancer(vitesse=50)
        direction_initiale = self.moteur.direction_actuelle
        
        self.faux_pwm.reset_mock()
        
        self.moteur.changer_vitesse(nouvelle_vitesse=75)
        
        self.assertEqual(self.moteur.pwm_applique, 75)
        self.assertEqual(self.moteur.direction_actuelle, direction_initiale)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(75)
    
    def test_changer_vitesse_au_dessous_seuil_leve_erreur(self):
        """changer_vitesse avec PWM < seuil lève ValueError"""
        self.moteur.avancer(vitesse=50)
        
        with self.assertRaises(ValueError) as context:
            self.moteur.changer_vitesse(nouvelle_vitesse=20)
        self.assertEqual(str(context.exception), "PWM 20% inférieur au seuil minimal 30%")
    
    # ========== TESTS ARRET ==========
    def test_arreter_met_pwm_a_zero(self):
        """Test que arreter() met PWM à 0 et apelle ChangeDutyCycle(0)"""
        self.moteur.avancer(vitesse=100)
        
        self.faux_gpio.reset_mock()
        self.faux_pwm.reset_mock()
        
        self.moteur.arreter()
        
        self.assertEqual(self.moteur.pwm_applique, 0)
        self.assertIsNone(self.moteur.direction_actuelle)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in1, False)
        self.faux_gpio.output.assert_any_call(self.moteur.pin_in2, False)
        self.faux_pwm.ChangeDutyCycle.assert_called_with(0)

    # ========== TESTS VALEURS INVALIDES ==========
    def test_vitesse_negative_leve_erreur(self):
        """Vitesse négative lève ValueError"""
        with self.assertRaises(ValueError) as context:
            self.moteur.avancer(vitesse=-10)
        self.assertEqual(str(context.exception), "Vitesse doit être entre 0 et 100")
    
    def test_vitesse_superieure_100_leve_erreur(self):
        """Vitesse > 100% lève ValueError"""
        with self.assertRaises(ValueError) as context:
            self.moteur.avancer(vitesse=150)
        self.assertEqual(str(context.exception), "Vitesse doit être entre 0 et 100")
