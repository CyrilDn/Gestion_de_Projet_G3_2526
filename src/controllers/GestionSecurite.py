import time

class GestionSecurite:
    # Geometrie du vehicule (cm)
    LARGEUR_VOITURE = 20
    LONGUEUR_VOITURE = 40

    # Marges minimales dans un couloir a murs lateraux
    MARGE_LATERALE_SECURITE = 4

    # Seuils de securite (cm)
    DISTANCE_URGENCE_AVANT = (LONGUEUR_VOITURE / 2) + 6  # ~26 cm
    DISTANCE_COLLISION_AVANT = 14
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

    # Parametres de pilotage
    GAIN_CENTRAGE = 1.3
    HYSTERESIS_CENTRAGE = 1.5
    CORRECTION_MAX_CENTRAGE = 45
    MAX_VARIATION_ANGLE_PAR_CYCLE = 5

    # 2 plages de braquage en evitement frontal
    ANGLE_GAUCHE_PROCHE = 67
    ANGLE_DROITE_PROCHE = 113
    BIAIS_PRIORITE_DROITE_CM = 5

    # Evite de garder un grand braquage trop longtemps
    SEUIL_VIRAGE_FORT = 24
    DUREE_MAX_VIRAGE_FORT = 0.7
    CORRECTION_APRES_TIMEOUT = 14

    # Parametres anti-blocage pour les virages serres (forme S)
    FENETRE_BLOCAGE_SECONDES = 2.2
    DISTANCE_SORTIE_BLOCAGE = 34
    COOLDOWN_APRES_RECUL = 0.25
    NB_TENTATIVES_INVERSION = 3
    ANGLE_RECUL_BASE = 12
    ANGLE_RECUL_RENFORCE = 20
    DUREE_RECUL_BASE = 0.35
    DUREE_RECUL_MAX = 0.75

    # Optimisations robustesse circuit complexe
    REDUCTION_BIAIS_PAR_TENTATIVE = 3
    BIAIS_PRIORITE_DROITE_MIN = -4
    NB_CYCLES_ASSIST_SORTIE = 5
    AMPLITUDE_ASSIST_SORTIE = 10
    DISTANCE_ANGLE_DIRECT = 30
    
    def __init__(self, controleur):
        """Initialiser les parametres de securite"""
        self.controleur = controleur
        self._angle_applique = self.ANGLE_TOUT_DROIT
        self._dernier_log = 0.0
        self._debut_virage_fort = None
        self._sens_virage_fort = 0
        self._compteur_deblocage = 0
        self._dernier_deblocage = 0.0
        self._fin_cooldown_recul = 0.0
        self._dernier_sens_recul = 1
        self._bias_priorite_droite_courant = self.BIAIS_PRIORITE_DROITE_CM
        self._assist_sortie_cycles_restants = 0
        self._assist_sortie_angle = self.ANGLE_TOUT_DROIT

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Retourne (vitesse, angle, mode) pour un pilotage fluide en couloir.
        mode in {"avance", "recul", "stop"}
        """
        distance_avant = self._normaliser_distance(distance1)
        distance_droite = self._normaliser_distance(distance2)
        distance_gauche = self._normaliser_distance(distance3)
        maintenant = time.time()

        # Quand la voie se degage, on remet progressivement l'etat anti-blocage a zero.
        if distance_avant is None or distance_avant > self.DISTANCE_SORTIE_BLOCAGE:
            self._compteur_deblocage = 0
            self._bias_priorite_droite_courant = self.BIAIS_PRIORITE_DROITE_CM
            self._assist_sortie_cycles_restants = 0

        # ETAPE 0: si bloque devant, reculer brievement en braquant vers le mur le plus proche
        if self._doit_debloquer_devant(distance_avant):
            if (
                maintenant >= self._fin_cooldown_recul
                or self._collision_imminente(distance_avant)
            ):
                tentative = self._mettre_a_jour_tentatives_deblocage(maintenant)
                angle_recul = self._choisir_angle_recul(
                    distance_droite, distance_gauche, tentative
                )
                duree_recul = self._calculer_duree_recul(distance_avant, tentative)
                self._ajuster_biais_dynamique(tentative)
                self._preparer_assist_sortie(angle_recul, tentative)
                self._appliquer_servo(angle_recul)
                self._fin_cooldown_recul = maintenant + self.COOLDOWN_APRES_RECUL
                return (
                    self.VITESSE_MARCHE_ARRIERE,
                    angle_recul,
                    "recul",
                    duree_recul,
                )

        # ETAPE 1: securite absolue
        if self._urgence(distance_avant, distance_droite, distance_gauche):
            print("[🛑] Obstacle critique detecte -> arret d'urgence")
            self.arreter_urgence()
            return None, self.ANGLE_TOUT_DROIT, "stop"

        # ETAPE 2: vitesse adaptee a la distance avant
        vitesse_moteur = self._calculer_vitesse(distance_avant, distance_droite, distance_gauche)

        # ETAPE 3: angle cible = centrage couloir + evitement avant
        angle_centrage = self._calculer_angle_centrage(distance_droite, distance_gauche)
        angle_cible = self._fusionner_evitement_avant(
            angle_centrage, distance_avant, distance_droite, distance_gauche
        )
        angle_cible = self._appliquer_assist_sortie(angle_cible)
        angle_cible = self._limiter_duree_virage(angle_cible)

        if self._doit_appliquer_angle_direct(distance_avant):
            angle_applique = self._borner_angle(angle_cible)
            self._angle_applique = float(angle_applique)
        else:
            angle_applique = self._lisser_angle(angle_cible)
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
        # Le frontal proche est traite par la manoeuvre de debloquage.
        # On ne garde l'urgence frontale que pour collision quasi-immediate.
        if d_avant is not None and d_avant < self.DISTANCE_COLLISION_AVANT:
            return True
        if d_droite is not None and d_droite < self.DISTANCE_URGENCE_LATERALE:
            return True
        if d_gauche is not None and d_gauche < self.DISTANCE_URGENCE_LATERALE:
            return True
        return False

    def _doit_debloquer_devant(self, d_avant):
        return d_avant is not None and d_avant < self.DISTANCE_URGENCE_AVANT

    def _collision_imminente(self, d_avant):
        if d_avant is None:
            return False
        return d_avant < (self.DISTANCE_COLLISION_AVANT + 2)

    def _mettre_a_jour_tentatives_deblocage(self, maintenant):
        if maintenant - self._dernier_deblocage <= self.FENETRE_BLOCAGE_SECONDES:
            self._compteur_deblocage += 1
        else:
            self._compteur_deblocage = 1
        self._dernier_deblocage = maintenant
        return self._compteur_deblocage

    def _choisir_angle_recul(self, d_droite, d_gauche, tentative):
        # Base: braquer vers le mur le plus proche.
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
            # Sans mesure laterale, on alterne pour casser les oscillations.
            sens = -self._dernier_sens_recul

        if tentative >= self.NB_TENTATIVES_INVERSION:
            # En S serre, inverser le sens apres plusieurs echecs debloque souvent la situation.
            sens *= -1

        amplitude = self.ANGLE_RECUL_BASE
        if tentative >= 2:
            amplitude = self.ANGLE_RECUL_RENFORCE

        self._dernier_sens_recul = sens
        return int(self.ANGLE_TOUT_DROIT + (sens * amplitude))

    def _calculer_duree_recul(self, d_avant, tentative):
        duree = self.DUREE_RECUL_BASE + (0.08 * min(max(tentative - 1, 0), 3))
        if d_avant is not None and d_avant < (self.DISTANCE_COLLISION_AVANT + 4):
            duree += 0.10
        return min(duree, self.DUREE_RECUL_MAX)

    def _ajuster_biais_dynamique(self, tentative):
        reduction = self.REDUCTION_BIAIS_PAR_TENTATIVE * max(tentative - 1, 0)
        self._bias_priorite_droite_courant = max(
            self.BIAIS_PRIORITE_DROITE_MIN,
            self.BIAIS_PRIORITE_DROITE_CM - reduction,
        )

    def _preparer_assist_sortie(self, angle_recul, tentative):
        sens_recul = 1 if angle_recul > self.ANGLE_TOUT_DROIT else (-1 if angle_recul < self.ANGLE_TOUT_DROIT else 0)
        if sens_recul == 0:
            self._assist_sortie_cycles_restants = 0
            return

        self._assist_sortie_angle = self.ANGLE_TOUT_DROIT - (sens_recul * self.AMPLITUDE_ASSIST_SORTIE)
        cycles_bonus = min(max(tentative - 2, 0), 2)
        self._assist_sortie_cycles_restants = self.NB_CYCLES_ASSIST_SORTIE + cycles_bonus

    def _appliquer_assist_sortie(self, angle_cible):
        if self._assist_sortie_cycles_restants <= 0:
            return angle_cible

        self._assist_sortie_cycles_restants -= 1
        poids_assist = 0.35
        return ((1.0 - poids_assist) * angle_cible) + (poids_assist * self._assist_sortie_angle)

    def _doit_appliquer_angle_direct(self, d_avant):
        return d_avant is not None and d_avant < self.DISTANCE_ANGLE_DIRECT

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

        # Si une paroi est tres proche sur le cote, on reduit encore un peu
        for cote in (d_droite, d_gauche):
            if cote is not None and cote < (self.DISTANCE_URGENCE_LATERALE + 3):
                vitesse = min(vitesse, self.VITESSE_RALENTI)

        return vitesse

    def _calculer_angle_centrage(self, d_droite, d_gauche):
        # Cas nominal: on centre la voiture dans le couloir
        if d_droite is not None and d_gauche is not None:
            # erreur < 0 => plus proche du mur droit => tourner a gauche (angle plus petit)
            erreur = d_droite - d_gauche
            somme = max(d_droite + d_gauche, 1.0)
            erreur_normalisee = erreur / somme
            if abs(erreur) < self.HYSTERESIS_CENTRAGE:
                correction = 0.0
            else:
                correction = max(
                    -self.CORRECTION_MAX_CENTRAGE,
                    min(
                        self.CORRECTION_MAX_CENTRAGE,
                        erreur_normalisee * self.GAIN_CENTRAGE * self.CORRECTION_MAX_CENTRAGE,
                    ),
                )
            return self.ANGLE_TOUT_DROIT + correction

        # Degrade proprement si une seule mesure laterale est disponible
        if d_droite is not None and d_droite < 20:
            return self.ANGLE_TOUT_DROIT - 8
        if d_gauche is not None and d_gauche < 20:
            return self.ANGLE_TOUT_DROIT + 8

        return self.ANGLE_TOUT_DROIT

    def _fusionner_evitement_avant(self, angle_centrage, d_avant, d_droite, d_gauche):
        if d_avant is None or d_avant >= self.DISTANCE_EVITEMENT_AVANT:
            return angle_centrage

        # 2 niveaux fixes uniquement:
        # - tres proche -> angle max (45 ou 135)
        # - proche raisonnable -> 67 ou 113
        if d_avant < self.DISTANCE_FREINAGE_FORT:
            angle_gauche = self.ANGLE_GAUCHE_MAX
            angle_droite = self.ANGLE_DROITE_MAX
        else:
            angle_gauche = self.ANGLE_GAUCHE_PROCHE
            angle_droite = self.ANGLE_DROITE_PROCHE

        if d_gauche is not None and d_droite is not None:
            # Priorite droite pour le sens du circuit, sauf si gauche est nettement plus libre.
            if d_droite >= (d_gauche - self._bias_priorite_droite_courant):
                angle_evitement = angle_droite
            else:
                angle_evitement = angle_gauche
        elif d_gauche is not None:
            angle_evitement = angle_gauche
        elif d_droite is not None:
            angle_evitement = angle_droite
        else:
            # En l'absence de mesures laterales fiables, on garde la priorite droite.
            angle_evitement = angle_droite
        return angle_evitement

    def _limiter_duree_virage(self, angle_cible):
        correction = angle_cible - self.ANGLE_TOUT_DROIT
        sens = 1 if correction > 0 else (-1 if correction < 0 else 0)
        maintenant = time.time()

        if abs(correction) >= self.SEUIL_VIRAGE_FORT:
            if self._sens_virage_fort != sens:
                self._sens_virage_fort = sens
                self._debut_virage_fort = maintenant
            elif self._debut_virage_fort is not None and (
                maintenant - self._debut_virage_fort > self.DUREE_MAX_VIRAGE_FORT
            ):
                correction = sens * min(abs(correction), self.CORRECTION_APRES_TIMEOUT)
        else:
            self._sens_virage_fort = 0
            self._debut_virage_fort = None

        return self.ANGLE_TOUT_DROIT + correction

    def _lisser_angle(self, angle_cible):
        angle_cible = max(self.ANGLE_GAUCHE_MAX, min(self.ANGLE_DROITE_MAX, angle_cible))
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