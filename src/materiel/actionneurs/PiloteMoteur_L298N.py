import RPi.GPIO as GPIO
import time

class PiloteMoteur_L298N:
    SEUIL_PWM_MINIMAL = 30 # PWM minimal 
    DELAI_INVERSION = 0.5  # Délai de sécurité avant inversion (secondes)
    
    def __init__(self, pin_in1, pin_in2, canal_pwm, pca=None):
        """Initialiser le pilote moteur L298N"""
        self._pin_in1 = pin_in1
        self._pin_in2 = pin_in2
        self._canal_pwm = canal_pwm
        self._pca = pca  # PCA9685 pour contrôler le PWM

        self._vitesse = 0  # Vitesse actuelle du moteur (0-100%)
        self._direction_actuelle = None 
        self._pwm_applique = 0  # Dernier PWM appliqué
        
        if self._pca is not None:
            self._initialiser_gpio()
    
    # Propriétés pour accéder aux attributs privés
    @property
    def vitesse(self):
        """Obtenir la vitesse actuelle du moteur"""
        return self._vitesse
    
    @property
    def direction_actuelle(self):
        """Obtenir la direction actuelle du moteur"""
        return self._direction_actuelle
    
    @property
    def pwm_applique(self):
        """Obtenir le dernier PWM appliqué"""
        return self._pwm_applique
    
    @property
    def pca(self):
        """Obtenir le contrôleur PCA9685"""
        return self._pca
    
    def _initialiser_gpio(self):
        """Initialiser les broches GPIO pour le contrôle du moteur"""
        if self._pca is None:
            raise ValueError("PCA9685 non fourni")
        
        # IN1 et IN2 pour contrôler la direction en sortie
        GPIO.setup(self._pin_in1, GPIO.OUT)
        GPIO.setup(self._pin_in2, GPIO.OUT)
        
        # Initialiser le canal PWM du PCA9685 à 0
        self._pca.set_pwm(self._canal_pwm, 0, 0)

    def _ramping_progressif(self, pwm_debut, pwm_fin, direction):
        """Effectuer un démarrage progressif du moteur pour éviter les chocs mécaniques"""
        if self._pca is None:
            raise ValueError("PCA9685 non initialisé")
        
        steps = 2
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
            self._ramping_progressif(self._pwm_applique, vitesse, "avancer")
        else:
            if self._direction_actuelle == "reculer" and self._pwm_applique > 0:
                time.sleep(self.DELAI_INVERSION)
            
            if self._pca is not None:
                GPIO.output(self._pin_in1, GPIO.HIGH)
                GPIO.output(self._pin_in2, GPIO.LOW)
                valeur_pwm = int((vitesse / 100) * 4095)
                self._pca.set_pwm(self._canal_pwm, 0, valeur_pwm)
            
            self._pwm_applique = vitesse
            self._direction_actuelle = "avancer"

    def reculer(self, vitesse=100, ramping=False):
        """Faire reculer: IN1=LOW, IN2=HIGH, PWM=vitesse"""
        if vitesse < 0 or vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        if vitesse > 0 and vitesse < self.SEUIL_PWM_MINIMAL:
            raise ValueError(f"PWM {vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
        
        if ramping:
            self._ramping_progressif(self._pwm_applique, vitesse, "reculer")
        else:
            if self._direction_actuelle == "avancer" and self._pwm_applique > 0:
                time.sleep(self.DELAI_INVERSION)

            if self._pca is not None:
                GPIO.output(self._pin_in1, GPIO.LOW)
                GPIO.output(self._pin_in2, GPIO.HIGH)
                valeur_pwm = int((vitesse / 100) * 4095)
                self._pca.set_pwm(self._canal_pwm, 0, valeur_pwm)

            self._pwm_applique = vitesse
            self._direction_actuelle = "reculer"

    def changer_vitesse(self, nouvelle_vitesse):
        """Changer la vitesse sans changer la direction"""
        if nouvelle_vitesse < 0 or nouvelle_vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        if nouvelle_vitesse > 0 and nouvelle_vitesse < self.SEUIL_PWM_MINIMAL:
            raise ValueError(f"PWM {nouvelle_vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
        
        if self._pca is not None:
            valeur_pwm = int((nouvelle_vitesse / 100) * 4095)
            self._pca.set_pwm(self._canal_pwm, 0, valeur_pwm)
        
        self._pwm_applique = nouvelle_vitesse

    def arreter(self):
        """Arrêter le moteur: IN1=LOW, IN2=LOW, PWM=0"""
        if self._pca is not None:
            GPIO.output(self._pin_in1, GPIO.LOW)
            GPIO.output(self._pin_in2, GPIO.LOW)
            self._pca.set_pwm(self._canal_pwm, 0, 0)
        
        self._direction_actuelle = None
        self._pwm_applique = 0

    def nettoyer(self):
        """Nettoyer les ressources GPIO"""
        self.arreter()
        GPIO.cleanup()