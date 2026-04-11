import time

class GestionSecurite:
    # Geometrie du vehicule (cm)
    LARGEUR_VOITURE = 20
    LONGUEUR_VOITURE = 40

    # Marges minimales dans un couloir a murs lateraux
    MARGE_LATERALE_SECURITE = 4

    # Seuils de securite (cm)
    DISTANCE_URGENCE_AVANT = (LONGUEUR_VOITURE / 2) + 6  # ~26 cm
    DISTANCE_URGENCE_LATERALE = (LARGEUR_VOITURE / 2) + MARGE_LATERALE_SECURITE  # ~14 cm
    DISTANCE_FREINAGE_FORT = 32
    DISTANCE_RALENTI_AVANT = 48
    DISTANCE_EVITEMENT_AVANT = 60

    # Vitesse (%)
    VITESSE_RAPIDE = 72
    VITESSE_NORMALE = 55
    VITESSE_RALENTI = 38
    VITESSE_FREINAGE = 24

    # Angles du servo (degres)
    ANGLE_TOUT_DROIT = 90
    ANGLE_MAX_GAUCHE = 116
    ANGLE_MAX_DROITE = 64

    # Parametres de pilotage
    GAIN_CENTRAGE = 1.3
    HYSTERESIS_CENTRAGE = 1.5
    CORRECTION_MAX_CENTRAGE = 15
    CORRECTION_EVITEMENT_MAX = 20
    MAX_VARIATION_ANGLE_PAR_CYCLE = 5
    
    def __init__(self, controleur):
        """Initialiser les parametres de securite"""
        self.controleur = controleur
        self._angle_applique = self.ANGLE_TOUT_DROIT
        self._dernier_log = 0.0

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Retourne (vitesse, angle) pour un pilotage fluide en couloir.
        Retourne (None, angle) si arret d'urgence declenche.
        """
        distance_avant = self._normaliser_distance(distance1)
        distance_droite = self._normaliser_distance(distance2)
        distance_gauche = self._normaliser_distance(distance3)

        # ETAPE 1: securite absolue
        if self._urgence(distance_avant, distance_droite, distance_gauche):
            print("[🛑] Obstacle critique detecte -> arret d'urgence")
            self.arreter_urgence()
            return None, self.ANGLE_TOUT_DROIT

        # ETAPE 2: vitesse adaptee a la distance avant
        vitesse_moteur = self._calculer_vitesse(distance_avant, distance_droite, distance_gauche)

        # ETAPE 3: angle cible = centrage couloir + evitement avant
        angle_centrage = self._calculer_angle_centrage(distance_droite, distance_gauche)
        angle_cible = self._fusionner_evitement_avant(
            angle_centrage, distance_avant, distance_droite, distance_gauche
        )

        angle_applique = self._lisser_angle(angle_cible)
        self._appliquer_servo(angle_applique)

        maintenant = time.time()
        if maintenant - self._dernier_log > 0.5:
            print(
                "[NAV] d_avant={:.1f} d_droite={:.1f} d_gauche={:.1f} -> v={} angle={}"
                .format(
                    distance_avant if distance_avant is not None else -1,
                    distance_droite if distance_droite is not None else -1,
                    distance_gauche if distance_gauche is not None else -1,
                    vitesse_moteur,
                    angle_applique,
                )
            )
            self._dernier_log = maintenant

        return vitesse_moteur, angle_applique
    
    def _normaliser_distance(self, distance):
        """Nettoyer une mesure ultrason (None si invalide)."""
        if distance is None:
            return None
        try:
            valeur = float(distance)
        except (TypeError, ValueError):
            return None

        if valeur <= 0:
            return None
        if valeur > 400:
            return 400.0
        return valeur

    def _urgence(self, d_avant, d_droite, d_gauche):
        if d_avant is not None and d_avant < self.DISTANCE_URGENCE_AVANT:
            return True
        if d_droite is not None and d_droite < self.DISTANCE_URGENCE_LATERALE:
            return True
        if d_gauche is not None and d_gauche < self.DISTANCE_URGENCE_LATERALE:
            return True
        return False

    def _calculer_vitesse(self, d_avant, d_droite, d_gauche):
        vitesse = self.VITESSE_RAPIDE

        if d_avant is not None:
            if d_avant < self.DISTANCE_FREINAGE_FORT:
                vitesse = self.VITESSE_FREINAGE
            elif d_avant < self.DISTANCE_RALENTI_AVANT:
                vitesse = self.VITESSE_RALENTI
            elif d_avant < self.DISTANCE_EVITEMENT_AVANT:
                vitesse = self.VITESSE_NORMALE

        # Si une paroi est tres proche sur le cote, on reduit encore un peu
        for cote in (d_droite, d_gauche):
            if cote is not None and cote < (self.DISTANCE_URGENCE_LATERALE + 3):
                vitesse = min(vitesse, self.VITESSE_RALENTI)

        return vitesse

    def _calculer_angle_centrage(self, d_droite, d_gauche):
        # Cas nominal: on centre la voiture dans le couloir
        if d_droite is not None and d_gauche is not None:
            erreur = d_gauche - d_droite
            if abs(erreur) < self.HYSTERESIS_CENTRAGE:
                correction = 0.0
            else:
                correction = max(
                    -self.CORRECTION_MAX_CENTRAGE,
                    min(self.CORRECTION_MAX_CENTRAGE, erreur * self.GAIN_CENTRAGE),
                )
            return self.ANGLE_TOUT_DROIT + correction

        # Degrade proprement si une seule mesure laterale est disponible
        if d_droite is not None and d_droite < 20:
            return self.ANGLE_TOUT_DROIT + 8
        if d_gauche is not None and d_gauche < 20:
            return self.ANGLE_TOUT_DROIT - 8

        return self.ANGLE_TOUT_DROIT

    def _fusionner_evitement_avant(self, angle_centrage, d_avant, d_droite, d_gauche):
        if d_avant is None or d_avant >= self.DISTANCE_EVITEMENT_AVANT:
            return angle_centrage

        # Plus l'obstacle avant est proche, plus on privilegie l'evitement.
        intensite = (self.DISTANCE_EVITEMENT_AVANT - d_avant) / (
            self.DISTANCE_EVITEMENT_AVANT - self.DISTANCE_FREINAGE_FORT
        )
        intensite = max(0.0, min(1.0, intensite))

        if d_gauche is not None and d_droite is not None:
            if d_gauche > d_droite + 2:
                angle_evitement = self.ANGLE_TOUT_DROIT + self.CORRECTION_EVITEMENT_MAX
            elif d_droite > d_gauche + 2:
                angle_evitement = self.ANGLE_TOUT_DROIT - self.CORRECTION_EVITEMENT_MAX
            else:
                angle_evitement = angle_centrage
        elif d_gauche is not None:
            angle_evitement = self.ANGLE_TOUT_DROIT + self.CORRECTION_EVITEMENT_MAX
        elif d_droite is not None:
            angle_evitement = self.ANGLE_TOUT_DROIT - self.CORRECTION_EVITEMENT_MAX
        else:
            angle_evitement = angle_centrage

        return (1.0 - intensite) * angle_centrage + intensite * angle_evitement

    def _lisser_angle(self, angle_cible):
        angle_cible = max(self.ANGLE_MAX_DROITE, min(self.ANGLE_MAX_GAUCHE, angle_cible))
        delta = angle_cible - self._angle_applique
        if abs(delta) > self.MAX_VARIATION_ANGLE_PAR_CYCLE:
            delta = self.MAX_VARIATION_ANGLE_PAR_CYCLE if delta > 0 else -self.MAX_VARIATION_ANGLE_PAR_CYCLE
        self._angle_applique += delta
        return int(round(self._angle_applique))

    def _appliquer_servo(self, angle):
        if self.controleur:
            self.controleur.obtenir_servo().positionner(int(angle))
    
    def verifier_securite_feu(self, couleur_dominante):
        """Vérifier les conditions de sécurité liées au feu de signalisation"""
        if couleur_dominante == "aucune":
            print("[⚠️] Aucune couleur détectée, possible problème de capteur")
            self.arreter_urgence()
            return False
        return True
    
    def arreter_urgence(self):
        """Arrêter tous les moteurs en cas d'urgence"""
        try:
            if self.controleur:
                print("[*] Arrêt d'urgence activé! Tous les moteurs arrêtés.")
                self.controleur.arreter_moteurs()
                self._angle_applique = self.ANGLE_TOUT_DROIT
                self.controleur.obtenir_servo().positionner(self.ANGLE_TOUT_DROIT)
        except Exception as e:
            print(f"[✗] Erreur lors de l'arrêt d'urgence: {e}")