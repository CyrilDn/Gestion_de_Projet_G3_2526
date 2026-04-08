class CapteurUltrason:
    MIN_PULSE_DURATION = 100e-6  # 100µs - seuil de distance minimale
    VITESSE_SON = 343  # m/s à 20°C
    SEUIL_VARIATION_BRUIT = 0.20  # 20% de variation = bruit/écho multiple
    
    def __init__(self, pin_trigger, pin_echo, lib_gpio=None):
        self.pin_trigger = pin_trigger
        self.pin_echo = pin_echo
        self.timeout = 0.02
        self.lib_gpio = lib_gpio  # Librairie GPIO pour la gestion des broches
    
    def mesurer_distance(self, pulse_duration):
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