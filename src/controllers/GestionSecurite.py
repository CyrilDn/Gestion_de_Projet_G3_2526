import time


class GestionSecurite:
    # Seuils de securite (cm)
    DISTANCE_MUR_BLOQUANT = 18
    DISTANCE_COLLISION_AVANT = 10
    DISTANCE_URGENCE_LATERALE = 0
    DISTANCE_FREINAGE_FORT = 32
    DISTANCE_RALENTI_AVANT = 48
    DISTANCE_EVITEMENT_AVANT = 60

    # Vitesse (%)
    VITESSE_RAPIDE = 72
    VITESSE_NORMALE = 55
    VITESSE_RALENTI = 38
    VITESSE_FREINAGE = 24
    VITESSE_MARCHE_ARRIERE = 35

    # Angles du servo (degres)
    ANGLE_TOUT_DROIT = 90
    ANGLE_GAUCHE_MAX = 45
    ANGLE_DROITE_MAX = 135

    # Parametres de pilotage simple
    HYSTERESIS_CENTRAGE = 2.0
    ANGLE_CORRECTION_LEGER = 10
    ANGLE_GAUCHE_PROCHE = 70
    ANGLE_DROITE_PROCHE = 110
    BIAIS_PRIORITE_DROITE_CM = 5
    DUREE_RECUL = 0.22
    
    def __init__(self, controleur):
        """Initialiser les parametres de securite"""
        self.controleur = controleur
        self._dernier_log = 0.0

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Retourne (vitesse, angle, mode) pour un pilotage simple et direct.
        mode in {"avance", "recul", "stop"}
        """
        distance_avant = self._normaliser_distance(distance1)
        distance_droite = self._normaliser_distance(distance2)
        distance_gauche = self._normaliser_distance(distance3)
        maintenant = time.time()

        # Petite marche arriere si la voiture est trop pres d'un mur frontal.
        if self._est_contre_mur(distance_avant):
            angle_recul = self._choisir_angle_recul(distance_droite, distance_gauche)
            self._appliquer_servo(angle_recul)
            return self.VITESSE_MARCHE_ARRIERE, angle_recul, "recul", self.DUREE_RECUL

        # ETAPE 1: securite absolue
        if self._urgence(distance_avant, distance_droite, distance_gauche):
            print("[🛑] Obstacle critique detecte -> arret d'urgence")
            self.arreter_urgence()
            return None, self.ANGLE_TOUT_DROIT, "stop"

        vitesse_moteur = self._calculer_vitesse(distance_avant, distance_droite, distance_gauche)
        angle_centrage = self._calculer_angle_centrage(distance_droite, distance_gauche)
        angle_applique = self._borner_angle(
            self._fusionner_evitement_avant(
                angle_centrage, distance_avant, distance_droite, distance_gauche
            )
        )
        self._appliquer_servo(angle_applique)

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

        return vitesse_moteur, angle_applique, "avance"
    
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
        if d_avant is not None and d_avant < self.DISTANCE_COLLISION_AVANT:
            return True
        if d_droite is not None and d_droite < self.DISTANCE_URGENCE_LATERALE:
            return True
        if d_gauche is not None and d_gauche < self.DISTANCE_URGENCE_LATERALE:
            return True
        return False

    def _est_contre_mur(self, d_avant):
        return d_avant is not None and d_avant <= self.DISTANCE_MUR_BLOQUANT

    def _choisir_angle_recul(self, d_droite, d_gauche):
        # Recul simple: braquer du cote oppose a l'espace libre principal.
        if d_droite is not None and d_gauche is not None:
            if d_droite < d_gauche:
                sens = 1
            else:
                sens = -1
        elif d_droite is not None:
            sens = 1
        elif d_gauche is not None:
            sens = -1
        else:
            sens = 1

        return int(self.ANGLE_TOUT_DROIT + (sens * 12))

    def _borner_angle(self, angle):
        return int(round(max(self.ANGLE_GAUCHE_MAX, min(self.ANGLE_DROITE_MAX, angle))))

    def _calculer_vitesse(self, d_avant, d_droite, d_gauche):
        vitesse = self.VITESSE_RAPIDE

        if d_avant is not None:
            if d_avant < self.DISTANCE_FREINAGE_FORT:
                vitesse = self.VITESSE_FREINAGE
            elif d_avant < self.DISTANCE_RALENTI_AVANT:
                vitesse = self.VITESSE_RALENTI
            elif d_avant < self.DISTANCE_EVITEMENT_AVANT:
                vitesse = self.VITESSE_NORMALE

        # Si une paroi est tres proche sur le cote, on reduit un peu.
        for cote in (d_droite, d_gauche):
            if cote is not None and cote < (self.DISTANCE_URGENCE_LATERALE + 3):
                vitesse = min(vitesse, self.VITESSE_RALENTI)

        return vitesse

    def _calculer_angle_centrage(self, d_droite, d_gauche):
        if d_droite is not None and d_gauche is not None:
            erreur = d_droite - d_gauche
            if abs(erreur) < self.HYSTERESIS_CENTRAGE:
                return self.ANGLE_TOUT_DROIT
            if erreur > 0:
                return self.ANGLE_TOUT_DROIT + self.ANGLE_CORRECTION_LEGER
            return self.ANGLE_TOUT_DROIT - self.ANGLE_CORRECTION_LEGER

        if d_droite is not None and d_droite < 20:
            return self.ANGLE_TOUT_DROIT - 8
        if d_gauche is not None and d_gauche < 20:
            return self.ANGLE_TOUT_DROIT + 8

        return self.ANGLE_TOUT_DROIT

    def _fusionner_evitement_avant(self, angle_centrage, d_avant, d_droite, d_gauche):
        if d_avant is None or d_avant >= self.DISTANCE_EVITEMENT_AVANT:
            return angle_centrage

        if d_avant < self.DISTANCE_FREINAGE_FORT:
            angle_gauche = self.ANGLE_GAUCHE_MAX
            angle_droite = self.ANGLE_DROITE_MAX
        else:
            angle_gauche = self.ANGLE_GAUCHE_PROCHE
            angle_droite = self.ANGLE_DROITE_PROCHE

        if d_gauche is not None and d_droite is not None:
            if d_droite >= (d_gauche - self.BIAIS_PRIORITE_DROITE_CM):
                angle_evitement = angle_droite
            else:
                angle_evitement = angle_gauche
        elif d_gauche is not None:
            angle_evitement = angle_gauche
        elif d_droite is not None:
            angle_evitement = angle_droite
        else:
            angle_evitement = angle_droite
        return angle_evitement

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
                self.controleur.obtenir_servo().positionner(self.ANGLE_TOUT_DROIT)
        except Exception as e:
            print(f"[✗] Erreur lors de l'arrêt d'urgence: {e}")