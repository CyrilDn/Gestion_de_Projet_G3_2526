class CapteurCouleur:
    SATURATION_SEUIL = 70000
    MIN_INTENSITE = 15
    SEUIL_DOMINANCE = 0.50 # 50% minimum pour être dominant
    SEUIL_SOMME_MIN = 10 

    def __init__(self, adresse_i2c, bus_i2c=None):
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
        self.sensor.gain = 1
        self.sensor.integration_time = 200
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

        # Si le clair est très faible, utiliser la valeur max des RGB comme référence
        if clair < 30:
            facteur = 255.0 / max(rouge, vert, bleu, 1)
        else:
            facteur = 255.0 / clair
        
        return (
            min(255, max(0, int(round(rouge * facteur)))),
            min(255, max(0, int(round(vert * facteur)))),
            min(255, max(0, int(round(bleu * facteur)))),
        )

    def detecter_couleur_dominante(self, rouge, vert, bleu, clair) -> str:
        """Détermine la couleur dominante à partir des valeurs RGB et du canal clair 
        en appliquant des seuils pour filtrer les conditions de saturation et de faible luminosité."""
        if rouge == 0 and vert == 0 and bleu == 0:
            return "aucune"

        if clair > self.SATURATION_SEUIL:
            return "saturation"

        somme = rouge + vert + bleu
        if somme < self.SEUIL_SOMME_MIN:
            return "trop_faible"

        r_ratio = rouge / somme
        g_ratio = vert  / somme
        b_ratio = bleu  / somme

        if r_ratio > self.SEUIL_DOMINANCE:
            return "rouge"
        if g_ratio > self.SEUIL_DOMINANCE:
            return "vert"
        if b_ratio > self.SEUIL_DOMINANCE:
            return "bleu"

        return "indéterminé"
