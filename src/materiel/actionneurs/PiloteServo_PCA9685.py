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
    def __init__(self, canal=0, angle_min=45, angle_max=135, pca=None, duty_min=0.03, duty_max=0.10):
        self.canal = canal
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.duty_min = duty_min  # Duty cycle min (3%)
        self.duty_max = duty_max  # Duty cycle max (10%)
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
            # Calculer le duty cycle directement (3-10% pour votre servo)
            # Convertir angle (0-180) en duty cycle (duty_min à duty_max)
            ratio = (angle_propre - self.angle_min) / (self.angle_max - self.angle_min)
            duty_cycle = self.duty_min + ratio * (self.duty_max - self.duty_min)
            
            # Envoyer au PCA9685
            pwm_value = int(duty_cycle * 65535)
            self.pca.channels[self.canal].duty_cycle = pwm_value
            
            self.dernier_angle = angle_propre
            return True
        except OSError as e:
            # Déclencher une réaction de sécurité si le signal PWM/I2C est instable ou perdu
            logging.error(f"Erreur critique de communication I2C : {e}")
            self.en_erreur = True
            return False
