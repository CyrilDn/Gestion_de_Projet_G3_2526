#import RPi.GPIO as GPIO
import time

class PiloteMoteur_L298N:
    SEUIL_PWM_MINIMAL = 30 # PWM minimal 
    DELAI_INVERSION = 0.5  # Délai de sécurité avant inversion (secondes)
    
    def __init__(self, pin_in1, pin_in2, pin_pwm, lib_gpio=None):
        self.pin_in1 = pin_in1
        self.pin_in2 = pin_in2
        self.pin_pwm = pin_pwm
        self.lib_gpio = lib_gpio

        self.vitesse = 0  # Vitesse actuelle du moteur (0-100%)
        self.direction_actuelle = None 
        self.pwm = None
        self.pwm_applique = 0  # Dernier PWM appliqué
        
        if self.lib_gpio is not None:
            self.initialiser_gpio()
    

    def initialiser_gpio(self):
        """Initialiser les broches GPIO pour le contrôle du moteur"""
        if self.lib_gpio is None:
            raise ValueError("Librairie GPIO non fournie")
        
        self.lib_gpio.setmode(self.lib_gpio.BCM)

        #IN1 et IN2 pour contrôler la direction en sortie
        self.lib_gpio.setup(self.pin_in1, self.lib_gpio.OUT)
        self.lib_gpio.setup(self.pin_in2, self.lib_gpio.OUT)

        # PWM pour contrôler la vitesse en sortie
        self.lib_gpio.setup(self.pin_pwm, self.lib_gpio.OUT)
        self.pwm = self.lib_gpio.PWM(self.pin_pwm, 1000)  # Fréquence de 1000Hz
        self.pwm.start(0)  # Démarrer avec une vitesse de 0% (arrêté)

    def _verifier_blocage(self):
        """Vérifier si le moteur est probablement bloqué
        
        Blocage détecté si:
        - PWM appliqué > 50% (haute demande de vitesse)
        - Vitesse réelle = 0% (moteur ne bouge pas du tout)
        """
        if self.pwm_applique > 50 and self.vitesse == 0:
            self.est_bloque = True
            return True
        else:
            self.est_bloque = False
            return False
        
    def _ramping_progressif(self, pwm_debut, pwm_fin, direction):
        """Effectuer un démarrage progressif du moteur pour éviter les chocs mécaniques
        
        Augmente progressivement le PWM de pwm_debut à pwm_fin en 5 étapes
        avec un délai de 0.1s entre chaque étape.
        """
        if self.lib_gpio is None or self.pwm is None:
            raise ValueError("Librairie GPIO ou PWM non initialisée")
        
        steps = 5
        step_delay = 0.1  # secondes
        pwm_step = (pwm_fin - pwm_debut) / steps
        
        for i in range(steps + 1):
            pwm_actuel = pwm_debut + i * pwm_step
            if direction == "avancer":
                self.avancer(vitesse=pwm_actuel, ramping=False)
            elif direction == "reculer":
                self.reculer(vitesse=pwm_actuel, ramping=False)
            time.sleep(step_delay)


    def avancer(self, vitesse=100, ramping=False):
        """Faire avancer: IN1=HIGH, IN2=LOW, PWM=vitesse
        
        Args:
            vitesse: Pourcentage de vitesse (0-100)
            ramping: Si True, applique un démarrage progressif
        """
        if ramping:
            self._ramping_progressif(self.pwm_applique, vitesse, "avancer")
        else:
            if vitesse < 0 or vitesse > 100:
                raise ValueError("Vitesse doit être entre 0 et 100")
            
            if vitesse > 0 and vitesse < self.SEUIL_PWM_MINIMAL:
                raise ValueError(f"PWM {vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
            
            # Délai avant inversion si direction différente
            if self.direction_actuelle == "reculer" and self.pwm_applique > 0:
                time.sleep(self.DELAI_INVERSION)
            
            if self.lib_gpio is not None:
                self.lib_gpio.output(self.pin_in1, True)
                self.lib_gpio.output(self.pin_in2, False)
                self.pwm.ChangeDutyCycle(vitesse)
            
            self.pwm_applique = vitesse
            self.direction_actuelle = "avancer"


    def reculer(self, vitesse=100, ramping=False):
        """Faire reculer: IN1=LOW, IN2=HIGH, PWM=vitesse
        
        Args:
            vitesse: Pourcentage de vitesse (0-100)
            ramping: Si True, applique un démarrage progressif
        """
        if ramping:
            self._ramping_progressif(self.pwm_applique, vitesse, "reculer")
        else:
            if vitesse < 0 or vitesse > 100:
                raise ValueError("Vitesse doit être entre 0 et 100")
            
            if vitesse > 0 and vitesse < self.SEUIL_PWM_MINIMAL:
                raise ValueError(f"PWM {vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
            
            # Délai avant inversion si direction différente
            if self.direction_actuelle == "avancer" and self.pwm_applique > 0:
                time.sleep(self.DELAI_INVERSION)

            if self.lib_gpio is not None:
                self.lib_gpio.output(self.pin_in1, False)
                self.lib_gpio.output(self.pin_in2, True)
                self.pwm.ChangeDutyCycle(vitesse)

            self.pwm_applique = vitesse
            self.direction_actuelle = "reculer"


    def changer_vitesse(self, nouvelle_vitesse):
        """Changer la vitesse sans changer la direction"""
        if nouvelle_vitesse < 0 or nouvelle_vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        if nouvelle_vitesse > 0 and nouvelle_vitesse < self.SEUIL_PWM_MINIMAL:
            raise ValueError(f"PWM {nouvelle_vitesse}% inférieur au seuil minimal {self.SEUIL_PWM_MINIMAL}%")
        
        if self.lib_gpio is not None and self.pwm is not None:
            self.pwm.ChangeDutyCycle(nouvelle_vitesse)
        
        self.pwm_applique = nouvelle_vitesse


    def arreter(self):
        """Arrêter le moteur: IN1=LOW, IN2=LOW, PWM=0"""
        if self.lib_gpio is not None:
            self.lib_gpio.output(self.pin_in1, False)
            self.lib_gpio.output(self.pin_in2, False)
            self.pwm.ChangeDutyCycle(0)
        
        self.direction_actuelle = None
        self.pwm_applique = 0

    def nettoyer(self):
        """Nettoyer les ressources GPIO"""
        self.arreter()
        if self.lib_gpio is not None:
            if self.pwm is not None:
                self.pwm.stop()
            self.lib_gpio.cleanup()