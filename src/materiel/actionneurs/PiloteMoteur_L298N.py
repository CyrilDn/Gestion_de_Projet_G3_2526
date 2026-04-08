#import RPi.GPIO as GPIO

class PiloteMoteur_L298N:
    def __init__(self, pin_1in, pin_in2, pin_pwm, lib_gpio=None):
        self.pin_1in = pin_1in
        self.pin_in2 = pin_in2
        self.pin_pwm = pin_pwm
        self.lib_gpio = lib_gpio
        self.vitesse = 0  # Vitesse actuelle du moteur (0-100%)
    
    def initialiser_gpio(self):
        if self.lib_gpio is None:
            raise ValueError("Librairie GPIO non fournie")
        
        self.lib_gpio.setmode(self.lib_gpio.BCM)

        #IN1 et IN2 pour contrôler la direction en sortie
        self.lib_gpio.setup(self.pin_1in, self.lib_gpio.OUT)
        self.lib_gpio.setup(self.pin_in2, self.lib_gpio.OUT)

        # PWM pour contrôler la vitesse en sortie
        self.lib_gpio.setup(self.pin_pwm, self.lib_gpio.OUT)
        self.pwm = self.lib_gpio.PWM(self.pin_pwm, 1000 )  # Fréquence de 1000Hz
        self.pwm.start(0)  # Démarrer avec une vitesse de 0% (arrêté)

    def avancer(self, vitesse=100):
        """Faire avancer: IN1=HIGH, IN2=LOW, PWM=vitesse"""
        if vitesse < 0 or vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")
        
        self.lib_gpio.output(self.pin_1in, True)
        self.lib_gpio.output(self.pin_in2, False)
        self.pwm.ChangeDutyCycle(vitesse)  # Régler la vitesse (0-100%)
        self.vitesse = vitesse  # Stocker la vitesse actuelle pour référence

    def reculer(self, vitesse=100):
        """Faire reculer: IN1=LOW, IN2=HIGH, PWM=vitesse"""
        if vitesse < 0 or vitesse > 100:
            raise ValueError("Vitesse doit être entre 0 et 100")

        self.lib_gpio.output(self.pin_1in, False)
        self.lib_gpio.output(self.pin_in2, True)
        self.pwm.ChangeDutyCycle(vitesse)  # Régler la vitesse (0-100%)
        self.vitesse = vitesse  # Stocker la vitesse actuelle pour référence

    def arreter(self):
        """Arrêter le moteur: IN1=LOW, IN2=LOW, PWM=0"""
        self.lib_gpio.output(self.pin_1in, False)
        self.lib_gpio.output(self.pin_in2, False)
        self.pwm.ChangeDutyCycle(0)  # Régler la vitesse à 0%
        self.vitesse = 0  # Stocker la vitesse actuelle pour référence
    
    def nettoyer(self):
        """Nettoyer les ressources GPIO"""
        if self.lib_gpio is not None:
            self.pwm.stop()  # Arrêter le PWM
            self.lib_gpio.cleanup()  # Nettoyer les ressources GPIO