class CapteurUltrason:
    def __init__(self, pin_trigger, pin_echo, lib_gpio=None):
        self.pin_trigger = pin_trigger
        self.pin_echo = pin_echo
        self.timeout = 0.02
        self.lib_gpio = lib_gpio  # Librairie GPIO pour la gestion des broches
    def mesurer_distance(self):
        # Code pour mesurer la distance à l'aide du capteur ultrason
        pass