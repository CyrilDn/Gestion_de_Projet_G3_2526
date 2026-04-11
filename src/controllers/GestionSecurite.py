import time

class GestionSecurite:
    # Constantes de sécurité
    DISTANCE_URGENCE = 0          # Distance critique côtés (0 = désactivé)
    DISTANCE_BLOQUE = 6           # Distance devant → manœuvre de dégagement
    DISTANCE_OBSTACLE_DEVANT = 20 # Obstacle devant → ralentir
    DISTANCE_OBSTACLE_COTE = 15   # Obstacle latéral → ralentir + braquer
    SEUIL_CENTRAGE = 8            # Écart entre côtés pour corriger la trajectoire (cm)

    # Constantes de vitesse
    VITESSE_RAPIDE = 40  # Voie libre
    VITESSE_RALENTI = 30 # Obstacle latéral ou devant (loin)
    VITESSE_FREINAGE = 25 # Obstacle devant très proche
    VITESSE_RECUL = 40   # Recul manœuvre de dégagement

    # Durée du recul lors d'une manœuvre de dégagement (secondes)
    DUREE_RECUL = 1.5

    # Angles du servo
    ANGLE_TOUT_DROIT = 90
    ANGLE_GAUCHE = 113
    ANGLE_DROITE = 67

    def __init__(self, controleur):
        """Initialiser les paramètres de sécurité"""
        self.controleur = controleur
        self.distance_securite = self.DISTANCE_URGENCE

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Vérifier les conditions de sécurité ET piloter la trajectoire.
        Retourne None si arrêt d'urgence déclenché, sinon retourne la vitesse (0-80).
        """

        # ÉTAPE 1 : Obstacles critiques latéraux → arrêt d'urgence immédiat
        if self.DISTANCE_URGENCE > 0:
            if (distance2 and distance2 < self.DISTANCE_URGENCE) or \
               (distance3 and distance3 < self.DISTANCE_URGENCE):
                print("[🛑] Obstacle CRITIQUE sur les côtés! Arrêt d'urgence immédiat!")
                self.arreter_urgence()
                return None

        # Voiture bloquée contre un mur devant → manœuvre de dégagement
        if distance1 and distance1 < self.DISTANCE_BLOQUE:
            print(f"[↩] Voiture bloquée devant ({distance1:.1f}cm) → Manœuvre de dégagement")
            self.manoeuvre_degagement(distance2, distance3)
            return 0

        # ÉTAPE 2 : Évaluer les obstacles et piloter
        vitesse_moteur = self.VITESSE_RAPIDE

        # Obstacle devant = PRIORITÉ MAXIMALE
        if distance1 and distance1 < self.DISTANCE_OBSTACLE_DEVANT:
            if distance1 < 12:
                vitesse_moteur = self.VITESSE_FREINAGE
                print(f"[⚠️] Obstacle TRÈS PROCHE devant ({distance1:.1f}cm) → Freinage FORT")
            else:
                vitesse_moteur = self.VITESSE_RALENTI
                print(f"[⚠️] Obstacle devant ({distance1:.1f}cm) → Ralentir")

            angle_servo = self._choisir_meilleure_direction(distance2, distance3)

            if angle_servo == self.ANGLE_GAUCHE:
                print("    → Tourner à GAUCHE")
            elif angle_servo == self.ANGLE_DROITE:
                print("    → Tourner à DROITE")

        # Pas d'obstacle devant → centrage actif + évitement latéral
        else:
            d_droite_proche = distance2 is not None and distance2 < self.DISTANCE_OBSTACLE_COTE
            d_gauche_proche = distance3 is not None and distance3 < self.DISTANCE_OBSTACLE_COTE

            if d_droite_proche and d_gauche_proche:
                # Couloir étroit → freiner + braquer vers le côté le moins bloqué
                vitesse_moteur = self.VITESSE_FREINAGE
                if distance2 <= distance3:
                    angle_servo = self.ANGLE_GAUCHE
                    print(f"[⚠️] Couloir étroit (D:{distance2:.0f}cm G:{distance3:.0f}cm) → Tourner GAUCHE")
                else:
                    angle_servo = self.ANGLE_DROITE
                    print(f"[⚠️] Couloir étroit (D:{distance2:.0f}cm G:{distance3:.0f}cm) → Tourner DROITE")

            elif d_droite_proche:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_GAUCHE
                print(f"[⚠️] Obstacle DROITE ({distance2:.0f}cm) → Tourner GAUCHE")

            elif d_gauche_proche:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_DROITE
                print(f"[⚠️] Obstacle GAUCHE ({distance3:.0f}cm) → Tourner DROITE")

            else:
                # Voie libre → centrage actif entre les deux murs
                vitesse_moteur = self.VITESSE_RAPIDE
                angle_servo = self._centrage_actif(distance2, distance3)

        # Appliquer l'angle au servo
        if self.controleur:
            self.controleur.obtenir_servo().positionner(angle_servo)

        return vitesse_moteur

    def _centrage_actif(self, distance_droite, distance_gauche):
        """
        Corriger en continu la trajectoire pour rester centré entre les deux murs.

        Logique :
          ecart = distance_droite - distance_gauche
          > 0  →  mur droit plus loin, voiture décalée à gauche  → braquer à droite
          < 0  →  mur droit plus proche, voiture décalée à droite → braquer à gauche
          ≈ 0  →  centré → tout droit
        """
        if distance_droite is None or distance_gauche is None:
            # Un seul capteur disponible → s'éloigner du mur visible
            if distance_droite is not None and distance_droite < self.DISTANCE_OBSTACLE_COTE:
                return self.ANGLE_GAUCHE
            if distance_gauche is not None and distance_gauche < self.DISTANCE_OBSTACLE_COTE:
                return self.ANGLE_DROITE
            return self.ANGLE_TOUT_DROIT

        ecart = distance_droite - distance_gauche

        if ecart > self.SEUIL_CENTRAGE:
            print(f"[→] Décalé à gauche (D:{distance_droite:.0f} G:{distance_gauche:.0f}) → Correction DROITE")
            return self.ANGLE_DROITE
        elif ecart < -self.SEUIL_CENTRAGE:
            print(f"[←] Décalé à droite (D:{distance_droite:.0f} G:{distance_gauche:.0f}) → Correction GAUCHE")
            return self.ANGLE_GAUCHE
        else:
            print(f"[✓] Centré (D:{distance_droite:.0f} G:{distance_gauche:.0f}) → Tout droit")
            return self.ANGLE_TOUT_DROIT

    def _choisir_meilleure_direction(self, distance_droite, distance_gauche):
        """
        Choisir la meilleure direction pour contourner un obstacle devant.
        Toujours retourne un côté (jamais tout droit si un mur est détecté devant).
        """
        if distance_gauche is not None and distance_droite is not None:
            if distance_gauche > distance_droite + 5:
                return self.ANGLE_GAUCHE
            elif distance_droite > distance_gauche + 5:
                return self.ANGLE_DROITE
            # Écart faible : choisir le moins bloqué
            return self.ANGLE_GAUCHE if distance_gauche >= distance_droite else self.ANGLE_DROITE

        if distance_gauche is not None:
            return self.ANGLE_GAUCHE if distance_gauche > self.DISTANCE_OBSTACLE_COTE else self.ANGLE_DROITE
        if distance_droite is not None:
            return self.ANGLE_DROITE if distance_droite > self.DISTANCE_OBSTACLE_COTE else self.ANGLE_GAUCHE

        return self.ANGLE_TOUT_DROIT

    def manoeuvre_degagement(self, distance_droite, distance_gauche):
        """
        Manœuvre de dégagement : reculer en tournant les roues vers le mur le plus proche
        afin que l'avant pivote dans la direction opposée et se remette droit.
        """
        if not self.controleur:
            return

        SEUIL_COTE_BLOQUE = 12

        # Déterminer le mur latéral le plus proche
        if distance_droite is not None and distance_gauche is not None:
            if distance_droite <= distance_gauche:
                angle_recul, cote = self.ANGLE_DROITE, "droite"
            else:
                angle_recul, cote = self.ANGLE_GAUCHE, "gauche"
        elif distance_droite is not None:
            angle_recul, cote = self.ANGLE_DROITE, "droite"
        elif distance_gauche is not None:
            angle_recul, cote = self.ANGLE_GAUCHE, "gauche"
        else:
            angle_recul, cote = self.ANGLE_TOUT_DROIT, "inconnu"

        # Sécurité : si le côté visé est lui-même trop proche, inverser
        if cote == "droite" and distance_droite is not None and distance_droite < SEUIL_COTE_BLOQUE:
            angle_recul = self.ANGLE_GAUCHE
            print(f"[↩] Droite trop proche ({distance_droite:.0f}cm) → braquage inversé GAUCHE")
        elif cote == "gauche" and distance_gauche is not None and distance_gauche < SEUIL_COTE_BLOQUE:
            angle_recul = self.ANGLE_DROITE
            print(f"[↩] Gauche trop proche ({distance_gauche:.0f}cm) → braquage inversé DROITE")
        else:
            print(f"[↩] Mur le plus proche : {cote} → recul roues braquées {cote}")

        self.controleur.arreter_moteurs()
        time.sleep(0.3)
        self.controleur.obtenir_servo().positionner(angle_recul)
        time.sleep(0.2)
        self.controleur.reculer_moteurs(vitesse=self.VITESSE_RECUL)
        time.sleep(self.DUREE_RECUL)
        self.controleur.arreter_moteurs()
        self.controleur.obtenir_servo().positionner(self.ANGLE_TOUT_DROIT)
        time.sleep(0.3)

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
                self.controleur.obtenir_servo().positionner(90)
        except Exception as e:
            print(f"[✗] Erreur lors de l'arrêt d'urgence: {e}")

__name__ = "__main__"
