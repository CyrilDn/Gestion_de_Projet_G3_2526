class PiloteMoteur_L298N:
    def __init__(self, pin_1in, pin_in2, pin_pwm, lib_gpio=None):
        self.pin_1in = pin_1in
        self.pin_in2 = pin_in2
        self.pin_pwm = pin_pwm
        self.lib_gpio = lib_gpio
    
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

    def avancer(self):
        # Code pour faire avancer le moteur
        pass

    def reculer(self):
        # Code pour faire reculer le moteur
        pass

    def arreter(self):
        # Code pour arrêter le moteur
        pass