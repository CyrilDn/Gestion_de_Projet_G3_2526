import logging

# Gestion de l'absence de la bibliothèque sur PC pour éviter les crashs d'importation
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
except ImportError:
    pass  # Sera géré par les Mocks dans les tests


class ServoDirectionPCA:
    def __init__(self, canal=0, angle_min=45, angle_max=135, pca=None, pulse_min=164, pulse_max=328):
        self.canal = canal
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.pulse_min = pulse_min  # Valeur pulse pour angle min (pour 45°)
        self.pulse_max = pulse_max  # Valeur pulse pour angle max (pour 135°)
        self.pulse_centre = 246     # Valeur pulse pour le centre (90°)
        self.dernier_angle = None
        self.en_erreur = False
        self.pca = pca

        try:
            # Utiliser le PCA9685 fourni ou en créer un nouveau
            if pca is None:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pca = PCA9685(i2c)
                self.pca.frequency = 50
            else:
                self.pca = pca
        except Exception as e:
            logging.error(f"Erreur d'initialisation I2C/PCA9685: {e}")
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
        Envoie la commande au PCA9685 avec vérification de stabilité et de signal.
        """
        if self.en_erreur:
            logging.error(
                "Sécurité : Action refusée, le contrôleur PCA9685 est hors ligne."
            )
            return False

        angle_propre = self.formater_angle(angle_brut)

        # Vérifier la stabilité (éviter de surcharger le bus I2C si l'angle est identique)
        if angle_propre == self.dernier_angle:
            return True  # Commande ignorée car déjà dans cette position

        try:
            # Calculer la valeur de pulse en fonction de l'angle
            # Interpoler linéairement entre pulse_min et pulse_max
            ratio = (angle_propre - self.angle_min) / (self.angle_max - self.angle_min)
            pulse_value = int(self.pulse_min + ratio * (self.pulse_max - self.pulse_min))
            
            # Envoyer au PCA9685 comme dans le code de test
            self.pca.channels[self.canal].duty_cycle = (pulse_value / 4095)
            
            self.dernier_angle = angle_propre
            return True
        except OSError as e:
            # Déclencher une réaction de sécurité si le signal PWM/I2C est instable ou perdu
            logging.error(f"Erreur critique de communication I2C : {e}")
            self.en_erreur = True
            return False
