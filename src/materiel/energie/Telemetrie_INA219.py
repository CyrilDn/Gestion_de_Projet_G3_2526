import logging
import board
import busio
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219


class Telemetrie_INA219:
    def __init__(self, adresse_i2c=0x40):
        self._adresse_i2c = adresse_i2c
        
        # Initialiser l'I2C et l'INA219
        i2c = busio.I2C(board.SCL, board.SDA)
        self._ina219 = INA219(i2c, addr=adresse_i2c)
        
        # Configuration de l'INA219
        self._ina219.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self._ina219.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self._ina219.bus_voltage_range = BusVoltageRange.RANGE_32V

        # Variables pour l'hystérésis de surcharge
        self._en_surcharge = False
        self._marge_hysteresis = 0.1

    # Getters
    def get_adresse_i2c(self) -> int:
        """Retourne l'adresse I2C."""
        return self._adresse_i2c

    def get_en_surcharge(self) -> bool:
        """Retourne l'état de surcharge."""
        return self._en_surcharge

    def get_marge_hysteresis(self) -> float:
        """Retourne la marge d'hystérésis."""
        return self._marge_hysteresis

    # Setters
    def set_marge_hysteresis(self, marge: float) -> None:
        """Définit la marge d'hystérésis."""
        if marge >= 0:
            self._marge_hysteresis = marge
        else:
            logging.warning("La marge d'hystérésis doit être positive")

    def lire_tension(self) -> float:
        """Lit la tension avec gestion d'erreur et retour de sécurité."""
        try:
            # Retourner la tension du bus en volts
            # Diviseur de tension : INA219 lit 29.04V pour 7.4V réel (2x3.7V)
            tension_brute = self._ina219.bus_voltage
            tension_reelle = tension_brute / 3.92
            return tension_reelle
        except Exception as e:
            logging.error(f"Timeout/Erreur lecture tension INA219 : {e}")
            return float("inf")

    def lire_courant(self) -> float:
        """Lit le courant avec gestion d'erreur et retour de sécurité."""
        try:
            # Retourner le courant en ampères
            return self._ina219.current / 1000.0  # Convertir mA en A
        except Exception as e:
            logging.error(f"Timeout/Erreur lecture courant INA219 : {e}")
            return float("inf")

    def verifier_surcharge(self, limite_courant: float) -> bool:
        """Vérifie si le moteur est en surcharge avec application d'une hystérésis."""
        courant_actuel = self.lire_courant()

        # Si une erreur de lecture s'est produite (valeur de sécurité retournée)
        if courant_actuel == float("inf"):
            self._en_surcharge = True
            return True

        if self._en_surcharge:
            # Règle d'hystérésis : pour sortir de la surcharge,
            # le courant doit descendre bien en dessous de la limite.
            if courant_actuel < (limite_courant - self._marge_hysteresis):
                self._en_surcharge = False
        else:
            # Pour entrer en surcharge, le courant doit dépasser strictement la limite.
            if courant_actuel > limite_courant:
                self._en_surcharge = True

        return self._en_surcharge
