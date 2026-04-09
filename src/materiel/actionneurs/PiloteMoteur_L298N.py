import RPi.GPIO as GPIO
import time

class PiloteMoteur_L298N:
    SEUIL_PWM_MINIMAL = 30 # PWM minimal 
    DELAI_INVERSION = 0.5  # Délai de sécurité avant inversion (secondes)
    
    def __init__(self, pin_in1, pin_in2, canal_pwm, pca=None):
        self.pin_in1 = pin_in1
        self.pin_in2 = pin_in2
        self.canal_pwm = canal_pwm
        self.pca = pca  # PCA9685 pour contrôler le PWM

        self.vitesse = 0  # Vitesse actuelle du moteur (0-100%)
        self.direction_actuelle = None 
        self.pwm_applique = 0  # Dernier PWM appliqué
        
        if self.pca is not None:
            self.initialiser_gpio()
    
    def initialiser_gpio(self):
        """Initialiser les broches GPIO pour le contrôle du moteur"""
        if self.pca is None:
            raise ValueError("PCA9685 non fourni")
        
        # IN1 et IN2 pour contrôler la direction en sortie
        GPIO.setup(self.pin_in1, GPIO.OUT)
        GPIO.setup(self.pin_in2, GPIO.OUT)
        
        # Initialiser le canal PWM du PCA9685 à 0
        self.pca.channels[self.canal_pwm].duty_cycle = 0

    def _ramping_progressif(self, pwm_debut, pwm_fin, direction):
        """Effectuer un démarrage progressif du moteur pour éviter les chocs mécaniques"""
        if self.pca is None:
            raise ValueError("PCA9685 non initialisé")
        
        steps = 5
        step_delay = 0.1
        pwm_step = (pwm_fin - pwm_debut) / steps
        
        for i in range(steps + 1):
            pwm_actuel = pwm_debut + i * pwm_step
            if direction == "avancer":
                self.avancer(vitesse=pwm_actuel, ramping=False)
            elif direction == "reculer":
                self.reculer(vitesse=pwm_actuel, ramping=False)
            time.sleep(step_delay)

            time.sleep(step_delay)

    def avancer(self, vitesse=100, ramping=False):
        """Faire avancer: IN1=HIGH, IN2=LOW, PWM=vitesse"""
        if vitesse < 0 or vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        if vitesse > 0 and vitesse < self.SEUIL_PWM_MINIMAL:
            raise ValueError(f"PWM {vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
        
        if ramping:
            self._ramping_progressif(self.pwm_applique, vitesse, "avancer")
        else:
            if self.direction_actuelle == "reculer" and self.pwm_applique > 0:
                time.sleep(self.DELAI_INVERSION)
            
            if self.pca is not None:
                GPIO.output(self.pin_in1, GPIO.HIGH)
                GPIO.output(self.pin_in2, GPIO.LOW)
                valeur_pwm = int((vitesse / 100) * 65535)
                self.pca.channels[self.canal_pwm].duty_cycle = valeur_pwm
            
            self.pwm_applique = vitesse
            self.direction_actuelle = "avancer"

    def reculer(self, vitesse=100, ramping=False):
        """Faire reculer: IN1=LOW, IN2=HIGH, PWM=vitesse"""
        if vitesse < 0 or vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        if vitesse > 0 and vitesse < self.SEUIL_PWM_MINIMAL:
            raise ValueError(f"PWM {vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
        
        if ramping:
            self._ramping_progressif(self.pwm_applique, vitesse, "reculer")
        else:
            if self.direction_actuelle == "avancer" and self.pwm_applique > 0:
                time.sleep(self.DELAI_INVERSION)

            if self.pca is not None:
                GPIO.output(self.pin_in1, GPIO.LOW)
                GPIO.output(self.pin_in2, GPIO.HIGH)
                valeur_pwm = int((vitesse / 100) * 65535)
                self.pca.channels[self.canal_pwm].duty_cycle = valeur_pwm

            self.pwm_applique = vitesse
            self.direction_actuelle = "reculer"

    def changer_vitesse(self, nouvelle_vitesse):
        """Changer la vitesse sans changer la direction"""
        if nouvelle_vitesse < 0 or nouvelle_vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        if nouvelle_vitesse > 0 and nouvelle_vitesse < self.SEUIL_PWM_MINIMAL:
            raise ValueError(f"PWM {nouvelle_vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
        
        if self.pca is not None:
            valeur_pwm = int((nouvelle_vitesse / 100) * 65535)
            self.pca.channels[self.canal_pwm].duty_cycle = valeur_pwm
        
        self.pwm_applique = nouvelle_vitesse

    def arreter(self):
        """Arrêter le moteur: IN1=LOW, IN2=LOW, PWM=0"""
        if self.pca is not None:
            GPIO.output(self.pin_in1, GPIO.LOW)
            GPIO.output(self.pin_in2, GPIO.LOW)
            self.pca.channels[self.canal_pwm].duty_cycle = 0
        
        self.direction_actuelle = None
        self.pwm_applique = 0

    def nettoyer(self):
        """Nettoyer les ressources GPIO"""
        self.arreter()
        GPIO.cleanup()