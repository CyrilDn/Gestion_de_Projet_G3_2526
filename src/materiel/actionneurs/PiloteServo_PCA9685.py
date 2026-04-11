import logging

try:
    import Adafruit_PCA9685
except ImportError:
    pass


class ServoDirectionPCA:
    def __init__(self, canal=0, angle_min=45, angle_max=135, pca=None, pulse_min=164, pulse_max=328):
        self._canal = canal
        self._angle_min = angle_min
        self._angle_max = angle_max
        self._pulse_min = pulse_min
        self._pulse_max = pulse_max
        self._pulse_centre = 246
        self._dernier_angle = None
        self._en_erreur = False
        self._pca = pca

        try:
            if pca is None:
                self._pca = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
                self._pca.set_pwm_freq(50)
            else:
                self._pca = pca
        except Exception as e:
            logging.error(f"Erreur d'initialisation PCA9685: {e}")
            self._en_erreur = True

    # Properties en lecture pour les attributs de configuration
    @property
    def canal(self):
        """Retourne le numéro du canal du servo."""
        return self._canal

    @property
    def angle_min(self):
        """Retourne l'angle minimum du servo."""
        return self._angle_min

    @property
    def angle_max(self):
        """Retourne l'angle maximum du servo."""
        return self._angle_max

    @property
    def pulse_min(self):
        """Retourne la valeur PWM minimale."""
        return self._pulse_min

    @property
    def pulse_max(self):
        """Retourne la valeur PWM maximale."""
        return self._pulse_max

    @property
    def dernier_angle(self):
        """Retourne le dernier angle positionnné."""
        return self._dernier_angle

    @property
    def en_erreur(self):
        """Indique si le servo est en état d'erreur."""
        return self._en_erreur

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
            return self._dernier_angle if self._dernier_angle is not None else 90

        # 2. Restriction à la plage (Clamp)
        if angle_calcule < self._angle_min:
            return self._angle_min
        elif angle_calcule > self._angle_max:
            return self._angle_max

        return angle_calcule

    def positionner(self, angle_brut):
        """
        Envoie la commande au PCA9685
        """
        if self._en_erreur:
            return False

        angle_propre = self.formater_angle(angle_brut)

        if angle_propre == self._dernier_angle:
            return True

        try:
            # Calculer pulse_value en fonction de l'angle
            ratio = (angle_propre - self._angle_min) / (self._angle_max - self._angle_min)
            pulse_value = int(self._pulse_min + ratio * (self._pulse_max - self._pulse_min))
            
            # Utiliser set_pwm comme dans le code de test
            self._pca.set_pwm(self._canal, 0, pulse_value)
            
            self._dernier_angle = angle_propre
            return True
        except Exception as e:
            logging.error(f"Erreur PCA9685: {e}")
            self._en_erreur = True
            return False
