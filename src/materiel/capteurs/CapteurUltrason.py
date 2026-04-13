import time
import RPi.GPIO as GPIO


class CapteurUltrason:
    MIN_PULSE_DURATION = 100e-6  # 100µs - seuil de distance minimale
    VITESSE_SON = 343  # m/s à 20°C
    SEUIL_VARIATION_BRUIT = 0.20  # 20% de variation = bruit/écho multiple
    PULSE_TRIGGER_DURATION = 10e-6  # 10µs - durée du pulse de déclenchement
    
    def __init__(self, pin_trigger, pin_echo, lib_gpio=GPIO):
        self._pin_trigger = pin_trigger
        self._pin_echo = pin_echo
        self._timeout = 0.1
        self._lib_gpio = lib_gpio
        
        if self._lib_gpio is not None:
            self._initialiser_gpio()
    
    def _initialiser_gpio(self):
        """Initialiser les pins GPIO (trigger en sortie, echo en entrée)"""
        if self._lib_gpio is None:
            raise RuntimeError("GPIO non fourni - impossible d'initialiser les pins")
        
        # PIN_TRIGGER en sortie, PIN_ECHO en entrée
        self._lib_gpio.setmode(self._lib_gpio.BCM) #BCM
        self._lib_gpio.setup(self._pin_trigger, self._lib_gpio.OUT) # Trigger 
        self._lib_gpio.setup(self._pin_echo, self._lib_gpio.IN) # Echo 
        
        # Initialiser le pin trigger à 0
        self._lib_gpio.output(self._pin_trigger, False)
    

    def _envoyer_pulse(self):
        """Envoyer un pulse de déclenchement et récupérer la durée de l'écho"""
        if self._lib_gpio is None:
            raise RuntimeError("GPIO non initialisé - impossible de mesurer")
        
        # Mettre le trigger à 0 et attendre la stabilisation (2ms suffisent pour le HC-SR04)
        self._lib_gpio.output(self._pin_trigger, False)
        time.sleep(0.002)
        
        # Envoyer un pulse de 10µs sur le trigger
        self._lib_gpio.output(self._pin_trigger, True)
        time.sleep(self.PULSE_TRIGGER_DURATION)
        self._lib_gpio.output(self._pin_trigger, False)
        
        # Attendre que echo passe à 1 (avec timeout absolu)
        debut = time.time()
        timeout = debut + self._timeout
        while self._lib_gpio.input(self._pin_echo) == 0:
            if time.time() > timeout:
                raise TimeoutError("Ultrason - Timeout: pas de réponse sur echo")
            debut = time.time()

        # Attendre que echo revienne à 0 (avec timeout absolu)
        fin = debut
        timeout = time.time() + self._timeout
        while self._lib_gpio.input(self._pin_echo) == 1:
            if time.time() > timeout:
                raise TimeoutError("Ultrason - Timeout: echo bloqué à 1")
            fin = time.time()

        # Calculer la durée du pulse
        pulse_duration = fin - debut
        return pulse_duration
    
    def mesurer_distance(self, pulse_duration=None):
        # Si pulse_duration n'est pas fourni, on mesure via GPIO
        if pulse_duration is None:
            pulse_duration = self._envoyer_pulse()
        
        # Cas limite: distance trop faible (durée < 100µs)
        if pulse_duration < self.MIN_PULSE_DURATION:
            raise ValueError("Ultrason - Distance trop faible: durée < 100µs")
        
        # Cas limite: timeout (durée > 30ms)
        if pulse_duration > self._timeout:
            raise TimeoutError("Ultrason - Timeout: durée > 30ms, aucun objet détecté")
        
        # Calculer la distance: distance = (vitesse * temps) / 2 (aller-retour)
        # distance en cm
        distance_cm = (self.VITESSE_SON * pulse_duration) / 2 * 100
        return distance_cm
    
    def nettoyer(self):
        """Nettoyer et libérer les ressources GPIO"""
        if self._lib_gpio is not None:
            self._lib_gpio.cleanup()

    # Propriétés pour accéder aux attributs privés
    @property
    def pin_trigger(self):
        """Récupérer le pin trigger"""
        return self._pin_trigger
    
    @property
    def pin_echo(self):
        """Récupérer le pin echo"""
        return self._pin_echo
    
    @property
    def timeout(self):
        """Récupérer le timeout"""
        return self._timeout
    
    @timeout.setter
    def timeout(self, valeur):
        """Définir le timeout"""
        if not isinstance(valeur, (int, float)) or valeur <= 0:
            raise ValueError("Timeout doit être un nombre positif")
        self._timeout = valeur
    
    @property
    def lib_gpio(self):
        """Récupérer la bibliothèque GPIO"""
        return self._lib_gpio