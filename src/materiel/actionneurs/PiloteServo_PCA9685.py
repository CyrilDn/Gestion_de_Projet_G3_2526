import logging

try:
    import Adafruit_PCA9685
except ImportError:
    pass


class ServoDirectionPCA:
    def __init__(
        self,
        canal=0,
        angle_min=45,
        angle_max=135,
        pca=None,
        pulse_min=164,
        pulse_max=328,
    ):
        self.canal = canal
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.pulse_min = pulse_min
        self.pulse_max = pulse_max
        self.pulse_centre = 246
        self.dernier_angle = None
        self.en_erreur = False
        self.pca = pca

        try:
            if pca is None:
                self.pca = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
                self.pca.set_pwm_freq(50)
            else:
                self.pca = pca
        except Exception as e:
            logging.error(f"Erreur d'initialisation PCA9685: {e}")
            self.en_erreur = True

    def formater_angle(self, angle_brut):
        """
        Gère l'arrondi, le cast et les limites de sécurité de l'angle.
        """
        try:
            # 1. Cast propre et arrondi (ex: "90.7" -> 90.7 -> 91)
            angle_calcule = int(round(float(angle_brut)))
        except (ValueError, TypeError, OverflowError):
            # En cas de donnée invalide (ex: un texte), on sécurise au centre ou au dernier angle
            logging.warning(f"Valeur d'angle invalide reçue : {angle_brut}. Ignorée.")
            return self.dernier_angle if self.dernier_angle is not None else 90

        # 2. Restriction à la plage (Clamp)
        if angle_calcule < self.angle_min:
            return self.angle_min
        elif angle_calcule > self.angle_max:
            return self.angle_max

        return angle_calcule

    def positionner(self, angle_brut):
        """
        Envoie la commande au PCA9685
        """
        if self.en_erreur:
            return False

        angle_brut -= 25
        angle_propre = self.formater_angle(angle_brut)

        if angle_propre == self.dernier_angle:
            return True

        try:
            # Calculer pulse_value en fonction de l'angle
            ratio = (angle_propre - self.angle_min) / (self.angle_max - self.angle_min)
            pulse_value = int(
                self.pulse_min + ratio * (self.pulse_max - self.pulse_min)
            )

            # Utiliser set_pwm comme dans le code de test
            self.pca.set_pwm(self.canal, 0, pulse_value)

            self.dernier_angle = angle_propre
            return True
        except Exception as e:
            logging.error(f"Erreur PCA9685: {e}")
            self.en_erreur = True
            return False
