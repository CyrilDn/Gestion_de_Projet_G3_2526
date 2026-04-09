import RPi.GPIO as GPIO


class CapteurCouleur:
    SATURATION_SEUIL = 60000
    MIN_INTENSITE = 15

    def __init__(self, adresse_i2c, bus_i2c=GPIO):
        self.adresse_i2c = int(str(adresse_i2c), 16)
        self.bus_i2c = bus_i2c
        self.sensor = None

    def initialiser(self):
        """Initialise le capteur via le bus I2C et la librairie Adafruit."""
        if self.bus_i2c is None:
            try:
                import board
            except ImportError as exc:
                raise ImportError("bibliothèque board introuvable") from exc
            self.bus_i2c = board.I2C()

        try:
            import adafruit_tcs34725
        except ImportError as exc:
            raise ImportError("bibliothèque adafruit_tcs34725 introuvable") from exc

        self.sensor = adafruit_tcs34725.TCS34725(self.bus_i2c)
        return self.sensor

    def lire_valeurs_brutes(self, sensor=None) -> tuple:
        """Retourne les valeurs brutes RGB et la luminosité claire."""
        if sensor is None:
            if self.sensor is None:
                raise ValueError("capteur non initialisé")
            sensor = self.sensor

        rouge, vert, bleu = getattr(sensor, "color_rgb_bytes", (0, 0, 0))
        clair = getattr(sensor, "clear", None)
        if clair is None:
            clair = getattr(sensor, "color_raw", (0, 0, 0, 0))[3]

        return int(rouge), int(vert), int(bleu), int(clair or 0)

    def normaliser_rgb(self, rouge, vert, bleu, clair) -> tuple:
        """Normalise les canaux RGB sur la base du canal clair."""
        if clair <= 0:
            return 0, 0, 0

        facteur = 255.0 / clair
        return (
            min(255, max(0, int(round(rouge * facteur)))),
            min(255, max(0, int(round(vert * facteur)))),
            min(255, max(0, int(round(bleu * facteur)))),
        )

    def detecter_couleur_dominante(self, rouge, vert, bleu, clair) -> str:
        """Détermine la couleur dominante à partir des valeurs RGB et du canal clair."""
        if rouge == 0 and vert == 0 and bleu == 0:
            return "aucune"

        if clair > self.SATURATION_SEUIL:
            return "saturation"

        normalises = self.normaliser_rgb(rouge, vert, bleu, clair)
        if max(normalises) < self.MIN_INTENSITE:
            return "trop_faible"

        index_dominant = normalises.index(max(normalises))
        return ["rouge", "vert", "bleu"][index_dominant]
