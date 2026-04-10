import RPi.GPIO as GPIO


class DetecteurLigneArrivee:
    def __init__(self, pin_capteur: int, lib_gpio= GPIO):
        self.pin_capteur = pin_capteur
        self.lib_gpio = lib_gpio

        # On suppose que la librairie possède un attribut IN (ex: RPi.GPIO.IN)
        self.lib_gpio.setup(self.pin_capteur, self.lib_gpio.IN)

    def est_sur_ligne_arrivee(self) -> bool:
        # Lit l'état du pin.
        etat = self.lib_gpio.input(self.pin_capteur)
        return bool(etat)
