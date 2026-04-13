import time


class GestionSecurite:
    # Distances en cm
    DISTANCE_URGENCE = 7
    DISTANCE_RECUL = 11
    DISTANCE_OBSTACLE_DEVANT = 20
    DISTANCE_ANTICIPATION = 35
    DISTANCE_OBSTACLE_COTE = 15
    DISTANCE_COUDE_SERRAGE = 11

    # Vitesses en pourcentage
    VITESSE_RAPIDE = 72
    VITESSE_NORMALE = 58
    VITESSE_RALENTI = 44
    VITESSE_FREINAGE = 34
    VITESSE_RECUL = 38
    VITESSE_RELANCE = 42

    # Angles servo
    ANGLE_TOUT_DROIT = 90
    ANGLE_GAUCHE = 113
    ANGLE_DROITE = 67

    # Reglages de trajectoire
    GAIN_CENTRAGE = 0.9
    CORRECTION_MAX = 18
    CORRECTION_ANTICIPATION_LEGERE = 8
    CORRECTION_ANTICIPATION_FORTE = 15
    DELTA_ANGLE_MAX = 12

    # Durees des manoeuvres en secondes
    DUREE_RECUL = 0.45
    DUREE_RELANCE = 0.55
    MAX_BLOCAGES_CONSECUTIFS = 4

    def __init__(self, controleur):
        """Initialiser les parametres de securite."""
        self.controleur = controleur
        self.distance_securite = self.DISTANCE_URGENCE
        self._phase_manoeuvre = None
        self._fin_manoeuvre = 0.0
        self._angle_recul = self.ANGLE_TOUT_DROIT
        self._angle_relance = self.ANGLE_TOUT_DROIT
        self._dernier_angle_commande = self.ANGLE_TOUT_DROIT
        self._derniere_direction_evitement = "droite"
        self._blocages_consecutifs = 0

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Analyser les distances et retourner une commande de conduite.

        Retour:
        - None si un arret d'urgence est declenche
        - dict(action=..., vitesse=..., angle=..., raison=...)
        """
        distance_avant = self._normaliser_distance(distance1)
        distance_droite = self._normaliser_distance(distance2)
        distance_gauche = self._normaliser_distance(distance3)

        commande_manoeuvre = self._obtenir_commande_manoeuvre()
        if commande_manoeuvre is not None:
            return commande_manoeuvre

        if distance_avant is not None and distance_avant < self.DISTANCE_RECUL:
            if self._passage_totalement_bloque(
                distance_avant, distance_droite, distance_gauche
            ):
                print("[STOP] Plusieurs blocages consecutifs -> arret d'urgence")
                self.arreter_urgence()
                return None
            return self._demarrer_manoeuvre_evitement(
                distance_avant, distance_droite, distance_gauche
            )

        if (
            distance_avant is not None
            and distance_avant < self.DISTANCE_OBSTACLE_DEVANT
            and self._ouverture_devant_trop_serree(distance_droite, distance_gauche)
        ):
            return self._demarrer_manoeuvre_evitement(
                distance_avant, distance_droite, distance_gauche
            )

        self._reinitialiser_blocages(distance_avant)
        return self._calculer_commande_avance(
            distance_avant, distance_droite, distance_gauche
        )

    def _calculer_commande_avance(
        self, distance_avant, distance_droite, distance_gauche
    ):
        """Calculer une avance plus progressive pour mieux tenir les virages."""
        vitesse = self.VITESSE_RAPIDE

        if distance_avant is not None:
            if distance_avant < self.DISTANCE_OBSTACLE_DEVANT:
                vitesse = self.VITESSE_RALENTI
            elif distance_avant < self.DISTANCE_ANTICIPATION:
                vitesse = self.VITESSE_NORMALE

        if self._cote_tres_proche(distance_droite, distance_gauche):
            vitesse = min(vitesse, self.VITESSE_RALENTI)

        correction = self._correction_centrage(distance_droite, distance_gauche)
        correction += self._correction_anticipation(
            distance_avant, distance_droite, distance_gauche
        )

        correction = max(-self.CORRECTION_MAX, min(self.CORRECTION_MAX, correction))
        angle = self._lisser_angle(self.ANGLE_TOUT_DROIT + correction)

        if distance_avant is not None and distance_avant < self.DISTANCE_OBSTACLE_DEVANT:
            print(
                f"[AVANT] Obstacle a {distance_avant:.1f} cm -> "
                f"vitesse {vitesse}% angle {angle}"
            )
        elif self._cote_tres_proche(distance_droite, distance_gauche):
            print(
                f"[COULOIR] Correction laterale -> vitesse {vitesse}% angle {angle}"
            )

        return self._creer_commande(
            action="avancer",
            vitesse=vitesse,
            angle=angle,
            raison="suivi_couloir",
        )

    def _obtenir_commande_manoeuvre(self):
        """Continuer une manoeuvre active de recul puis de relance."""
        if self._phase_manoeuvre is None:
            return None

        maintenant = time.time()
        if maintenant < self._fin_manoeuvre:
            if self._phase_manoeuvre == "recul":
                return self._creer_commande(
                    action="reculer",
                    vitesse=self.VITESSE_RECUL,
                    angle=self._angle_recul,
                    raison="recul_evitement",
                )

            return self._creer_commande(
                action="avancer",
                vitesse=self.VITESSE_RELANCE,
                angle=self._angle_relance,
                raison="relance_evitement",
            )

        if self._phase_manoeuvre == "recul":
            self._phase_manoeuvre = "relance"
            self._fin_manoeuvre = maintenant + self.DUREE_RELANCE
            direction = self._libelle_direction(self._derniere_direction_evitement)
            print(f"[EVITEMENT] Fin du recul -> relance vers la {direction}")
            return self._creer_commande(
                action="avancer",
                vitesse=self.VITESSE_RELANCE,
                angle=self._angle_relance,
                raison="relance_evitement",
            )

        self._phase_manoeuvre = None
        return None

    def _demarrer_manoeuvre_evitement(
        self, distance_avant, distance_droite, distance_gauche
    ):
        """Demarrer un recul court puis une relance dans la direction la plus libre."""
        direction = self._choisir_cote_evitement(distance_droite, distance_gauche)
        self._derniere_direction_evitement = direction
        self._phase_manoeuvre = "recul"
        self._fin_manoeuvre = time.time() + self._duree_recul(distance_avant)
        self._blocages_consecutifs += 1

        if self._couloir_tres_serre(distance_droite, distance_gauche):
            self._angle_recul = self.ANGLE_TOUT_DROIT
            self._angle_relance = (
                self.ANGLE_DROITE if direction == "droite" else self.ANGLE_GAUCHE
            )
        elif direction == "droite":
            self._angle_recul = self.ANGLE_GAUCHE
            self._angle_relance = self.ANGLE_DROITE
        else:
            self._angle_recul = self.ANGLE_DROITE
            self._angle_relance = self.ANGLE_GAUCHE

        print(
            f"[EVITEMENT] Obstacle devant ({distance_avant:.1f} cm) -> "
            f"recul puis sortie par la {self._libelle_direction(direction)} "
            f"(essai {self._blocages_consecutifs}/{self.MAX_BLOCAGES_CONSECUTIFS})"
        )

        return self._creer_commande(
            action="reculer",
            vitesse=self.VITESSE_RECUL,
            angle=self._angle_recul,
            raison="recul_evitement",
        )

    def _correction_centrage(self, distance_droite, distance_gauche):
        """Recentrer la voiture entre les bords quand le couloir se resserre."""
        if distance_droite is not None and distance_gauche is not None:
            difference = distance_gauche - distance_droite
            if abs(difference) <= 2:
                return 0
            return difference * self.GAIN_CENTRAGE

        if distance_droite is not None and distance_droite < self.DISTANCE_OBSTACLE_COTE:
            return self.CORRECTION_ANTICIPATION_LEGERE

        if distance_gauche is not None and distance_gauche < self.DISTANCE_OBSTACLE_COTE:
            return -self.CORRECTION_ANTICIPATION_LEGERE

        return 0

    def _correction_anticipation(self, distance_avant, distance_droite, distance_gauche):
        """Forcer un braquage plus net quand l'avant commence a se fermer."""
        if distance_avant is None or distance_avant >= self.DISTANCE_ANTICIPATION:
            return 0

        direction = self._choisir_cote_evitement(distance_droite, distance_gauche)
        amplitude = self.CORRECTION_ANTICIPATION_LEGERE
        if distance_avant < self.DISTANCE_OBSTACLE_DEVANT:
            amplitude = self.CORRECTION_ANTICIPATION_FORTE

        return -amplitude if direction == "droite" else amplitude

    def _choisir_cote_evitement(self, distance_droite, distance_gauche):
        """Choisir le cote le plus ouvert. En cas d'egalite, garder le dernier choix."""
        droite = self._distance_ou_infini(distance_droite)
        gauche = self._distance_ou_infini(distance_gauche)

        if abs(droite - gauche) <= 3:
            return self._derniere_direction_evitement

        return "droite" if droite > gauche else "gauche"

    def _ouverture_devant_trop_serree(self, distance_droite, distance_gauche):
        """Detecter un coude serre ou une epingle qui se ferme devant la voiture."""
        meilleure_ouverture = max(
            self._distance_ou_infini(distance_droite),
            self._distance_ou_infini(distance_gauche),
        )
        return meilleure_ouverture < self.DISTANCE_COUDE_SERRAGE

    def _passage_totalement_bloque(
        self, distance_avant, distance_droite, distance_gauche
    ):
        """Cas limite: plus aucune echappatoire fiable."""
        return (
            self._blocages_consecutifs >= self.MAX_BLOCAGES_CONSECUTIFS
            and distance_avant is not None
            and distance_avant < self.DISTANCE_URGENCE
            and self._couloir_tres_serre(distance_droite, distance_gauche)
        )

    def _couloir_tres_serre(self, distance_droite, distance_gauche):
        """Detecter une zone ou les deux flancs sont tres proches."""
        return (
            distance_droite is not None
            and distance_droite < self.DISTANCE_OBSTACLE_COTE
            and distance_gauche is not None
            and distance_gauche < self.DISTANCE_OBSTACLE_COTE
        )

    def _reinitialiser_blocages(self, distance_avant):
        """Oublier les blocages apres avoir retrouve de l'espace devant."""
        if distance_avant is None or distance_avant >= self.DISTANCE_ANTICIPATION:
            self._blocages_consecutifs = 0

    def _cote_tres_proche(self, distance_droite, distance_gauche):
        """Indiquer si un bord est suffisamment proche pour ralentir."""
        return (
            distance_droite is not None
            and distance_droite < self.DISTANCE_OBSTACLE_COTE
        ) or (
            distance_gauche is not None
            and distance_gauche < self.DISTANCE_OBSTACLE_COTE
        )

    def _duree_recul(self, distance_avant):
        """Allonger legerement le recul si l'obstacle est tres proche."""
        if distance_avant is not None and distance_avant <= self.DISTANCE_URGENCE:
            return self.DUREE_RECUL + 0.15
        return self.DUREE_RECUL

    def _lisser_angle(self, angle):
        """Limiter les changements trop brutaux d'un cycle a l'autre."""
        angle = int(round(angle))
        if angle > self._dernier_angle_commande + self.DELTA_ANGLE_MAX:
            angle = self._dernier_angle_commande + self.DELTA_ANGLE_MAX
        elif angle < self._dernier_angle_commande - self.DELTA_ANGLE_MAX:
            angle = self._dernier_angle_commande - self.DELTA_ANGLE_MAX

        angle = max(self.ANGLE_DROITE, min(self.ANGLE_GAUCHE, angle))
        self._dernier_angle_commande = angle
        return angle

    def _creer_commande(self, action, vitesse, angle, raison):
        """Uniformiser la structure de commande envoyee au controleur."""
        return {
            "action": action,
            "vitesse": int(round(vitesse)),
            "angle": int(round(angle)),
            "raison": raison,
        }

    def _distance_ou_infini(self, distance):
        """Utiliser une grande distance pour les capteurs absents ou hors plage."""
        if distance is None:
            return 400
        return distance

    def _normaliser_distance(self, distance):
        """Nettoyer une mesure brute avant de l'utiliser dans les decisions."""
        if distance is None:
            return None

        try:
            distance = float(distance)
        except (TypeError, ValueError):
            return None

        if distance <= 0:
            return None

        return distance

    def _libelle_direction(self, direction):
        """Renvoyer un libelle lisible pour les logs."""
        return "droite" if direction == "droite" else "gauche"

    def verifier_securite_feu(self, couleur_dominante):
        """Verifier les conditions de securite liees au feu de signalisation."""
        if couleur_dominante == "aucune":
            print("[FEU] Aucune couleur detectee, arret d'urgence")
            self.arreter_urgence()
            return False
        return True

    def arreter_urgence(self):
        """Arreter tous les moteurs en cas d'urgence."""
        try:
            if self.controleur:
                print("[STOP] Arret d'urgence active")
                self.controleur.arreter_moteurs()
                servo = self.controleur.obtenir_servo()
                if servo:
                    servo.positionner(self.ANGLE_TOUT_DROIT)
        except Exception as e:
            print(f"[ERREUR] Arret d'urgence impossible: {e}")


__name__ = "__main__"
