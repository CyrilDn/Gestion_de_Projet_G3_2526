import logging
import time


class Telemetrie_INA219:
    def __init__(self, adresse_i2c: str, bus_i2c: object):
        self.adresse_i2c = adresse_i2c
        self.bus_i2c = bus_i2c

        # Variables pour l'hystérésis de surcharge
        self.en_surcharge = False
        self.marge_hysteresis = 0.1

        # Configuration hypothétique du capteur
        # self.bus_i2c.write_byte(self.adresse_i2c, CONFIG_REGISTER)

    def lire_tension(self) -> float:
        """Lit la tension avec gestion d'erreur et retour de sécurité."""
        try:
            # Simulation d'une lecture sur le bus I2C (ex: smbus ou adafruit_bus_device)
            tension = self.bus_i2c.read_voltage(self.adresse_i2c)
            return tension
        except Exception as e:
            logging.error(f"Timeout/Erreur lecture tension INA219 : {e}")
            # Retourne une tension infinie pour forcer la désactivation des moteurs
            return float("inf")

    def lire_courant(self) -> float:
        """Lit le courant avec gestion d'erreur et retour de sécurité."""
        try:
            courant = self.bus_i2c.read_current(self.adresse_i2c)
            return courant
        except Exception as e:
            logging.error(f"Timeout/Erreur lecture courant INA219 : {e}")
            # Retourne un courant infini pour simuler une surcharge extrême et couper les moteurs
            return float("inf")

    def verifier_surcharge(self, limite_courant: float) -> bool:
        """Vérifie si le moteur est en surcharge avec application d'une hystérésis."""
        courant_actuel = self.lire_courant()

        # Si une erreur de lecture s'est produite (valeur de sécurité retournée)
        if courant_actuel == float("inf"):
            self.en_surcharge = True
            return True

        if self.en_surcharge:
            # Règle d'hystérésis : pour sortir de la surcharge,
            # le courant doit descendre bien en dessous de la limite.
            if courant_actuel < (limite_courant - self.marge_hysteresis):
                self.en_surcharge = False
        else:
            # Pour entrer en surcharge, le courant doit dépasser strictement la limite.
            if courant_actuel > limite_courant:
                self.en_surcharge = True

        return self.en_surcharge
