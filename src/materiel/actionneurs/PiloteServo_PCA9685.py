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
    def __init__(self, canal=0, angle_min=45, angle_max=135):
        self.canal = canal
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.dernier_angle = None
        self.en_erreur = False

        try:
            # Initialisation de la communication I2C et du module PCA9685
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(i2c)
            self.pca.frequency = 50

            # Création de l'objet servo sur le canal spécifié
            self.servo_moteur = servo.Servo(
                self.pca.channels[self.canal]
            )  # lie un canal specifique de la carte PCA9685 a un Object "moteur" Pyhton
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

        # 3. Vérifier la stabilité (éviter de surcharger le bus I2C si l'angle est identique)
        if angle_propre == self.dernier_angle:
            return True  # Commande ignorée car déjà dans cette position

        try:
            # 4. Envoi de la commande I2C
            self.servo_moteur.angle = angle_propre
            self.dernier_angle = angle_propre
            return True
        except OSError as e:
            # 5. Déclencher une réaction de sécurité si le signal PWM/I2C est instable ou perdu
            logging.error(f"Erreur critique de communication I2C : {e}")
            self.en_erreur = True
            # Ici, on pourrait déclencher l'arrêt d'urgence des moteurs de propulsion
            return False
