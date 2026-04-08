import time
#import RPi.GPIO as GPIO


class CapteurUltrason:
    MIN_PULSE_DURATION = 100e-6  # 100µs - seuil de distance minimale
    VITESSE_SON = 343  # m/s à 20°C
    SEUIL_VARIATION_BRUIT = 0.20  # 20% de variation = bruit/écho multiple
    PULSE_TRIGGER_DURATION = 10e-6  # 10µs - durée du pulse de déclenchement
    
    def __init__(self, pin_trigger, pin_echo, lib_gpio=None):
        self.pin_trigger = pin_trigger
        self.pin_echo = pin_echo
        self.timeout = 0.03
        self.lib_gpio = lib_gpio
        self._initialiser_gpio()
    
    def _initialiser_gpio(self):
        """Initialiser les pins GPIO (trigger en sortie, echo en entrée)"""
        if self.lib_gpio is None:
            raise RuntimeError("GPIO non fourni - impossible d'initialiser les pins")
        
        # PIN_TRIGGER en sortie, PIN_ECHO en entrée
        self.lib_gpio.setmode(self.lib_gpio.BCM) #BCM
        self.lib_gpio.setup(self.pin_trigger, self.lib_gpio.OUT) # Trigger 
        self.lib_gpio.setup(self.pin_echo, self.lib_gpio.IN) # Echo 
        
        # Initialiser le pin trigger à 0
        self.lib_gpio.output(self.pin_trigger, False)
    

    def _envoyer_pulse(self):
        """Envoyer un pulse de déclenchement et récupérer la durée de l'écho"""
        if self.lib_gpio is None:
            raise RuntimeError("GPIO non initialisé - impossible de mesurer")
        
        # Mettre le trigger à 0
        self.lib_gpio.output(self.pin_trigger, False)
        time.sleep(0.00001)  # Attendre 10µs
        
        # Envoyer un pulse de 10µs sur le trigger
        self.lib_gpio.output(self.pin_trigger, True)
        time.sleep(self.PULSE_TRIGGER_DURATION)
        self.lib_gpio.output(self.pin_trigger, False)
        
        # Mesurer la durée du signal sur echo
        start_time = time.time()
        start_wait = start_time
        
        # Attendre que echo passe à 1
        while self.lib_gpio.input(self.pin_echo) == 0:
            start_time = time.time()
            if start_time - start_wait > self.timeout:
                raise TimeoutError("Ultrason - Timeout: pas de réponse sur echo")
        
        # Attendre que echo revienne à 0
        start_wait = time.time()
        while self.lib_gpio.input(self.pin_echo) == 1:
            end_time = time.time()
            if end_time - start_wait > self.timeout:
                raise TimeoutError("Ultrason - Timeout: signal echo trop long")
        
        # Calculer la durée du pulse
        pulse_duration = end_time - start_time
        return pulse_duration
    
    def mesurer_distance(self, pulse_duration=None):
        # Si pulse_duration n'est pas fourni, on mesure via GPIO
        if pulse_duration is None:
            pulse_duration = self._envoyer_pulse()
        
        # Cas limite: distance trop faible (durée < 100µs)
        if pulse_duration < self.MIN_PULSE_DURATION:
            raise ValueError("Ultrason - Distance trop faible: durée < 100µs")
        
        # Cas limite: timeout (durée > 30ms)
        if pulse_duration > self.timeout:
            raise TimeoutError("Ultrason - Timeout: durée > 30ms, aucun objet détecté")
        
        # Calculer la distance: distance = (vitesse * temps) / 2 (aller-retour)
        # distance en cm
        distance_cm = (self.VITESSE_SON * pulse_duration) / 2 * 100
        return distance_cm
    
    def nettoyer(self):
        """Nettoyer et libérer les ressources GPIO"""
        if self.lib_gpio is not None:
            self.lib_gpio.cleanup()