import RPi.GPIO as GPIO


class DetecteurLigneArrivee:
    def __init__(self, pin_capteur: int, lib_gpio= GPIO):
        self._pin_capteur = pin_capteur
        self._lib_gpio = lib_gpio

        # On suppose que la librairie possède un attribut IN (ex: RPi.GPIO.IN)
        self._lib_gpio.setup(self._pin_capteur, self._lib_gpio.IN)

    @property
    def pin_capteur(self) -> int:
        """Obtient le numéro du pin du capteur."""
        return self._pin_capteur

    @property
    def lib_gpio(self):
        """Obtient la librairie GPIO utilisée."""
        return self._lib_gpio

    def est_sur_ligne_arrivee(self) -> bool:
        """Vérifie si la voiture est sur la ligne d'arrivée.
        
        Returns:
            bool: True si le capteur détecte la ligne d'arrivée, False sinon.
        """
        # Lit l'état du pin.
        etat = self._lib_gpio.input(self._pin_capteur)
        return bool(etat)
