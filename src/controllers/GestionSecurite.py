import time

class GestionSecurite:
    # Constantes de sécurité
    DISTANCE_URGENCE = 0 # Distance critique (arrêt immédiat)
    DISTANCE_OBSTACLE_DEVANT = 20 # Obstacle devant détecté
    DISTANCE_OBSTACLE_COTE = 15 # Obstacle sur les côtés
    DISTANCE_MUR_PROCHE = 8 # Distance pour enclencher le recul
    
    # Constantes de vitesse
    VITESSE_RAPIDE = 30 # Pas d'obstacle
    VITESSE_NORMALE = 25 # Obstacle éloigné
    VITESSE_RALENTI = 18 # Obstacle modéré
    VITESSE_FREINAGE = 13 # Obstacle proche
    
    # Angles du servo
    ANGLE_TOUT_DROIT = 90
    ANGLE_GAUCHE = 67
    ANGLE_DROITE = 113

    
    def __init__(self, controleur):
        """Initialiser les paramètres de sécurité"""
        self.controleur = controleur
        self.distance_securite = self.DISTANCE_URGENCE
        self.derniere_direction = self.ANGLE_TOUT_DROIT  # Mémoriser la dernière direction
        self.en_phase_recul = False  # Flag pour savoir si on est en train de reculer
        self.temps_recul_debut = 0  # Timestamp du début du recul

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Vérifier les conditions de sécurité ET traiter les obstacles
        Retourne None si arrêt d'urgence déclenché, sinon retourne la vitesse (0-50)
        """
        
        # ÉTAPE 0 : Gérer la phase de recul si active
        if self.en_phase_recul:
            temps_ecoule = time.time() - self.temps_recul_debut
            if temps_ecoule < 0.8:  # Reculer pendant 0.8 secondes
                print(f"[↶] Recul en cours... ({temps_ecoule:.2f}s)")
                if self.controleur:
                    self.controleur._moteur1.reculer(vitesse=25)
                    self.controleur._moteur2.reculer(vitesse=25)
                return 0  # Retourner 0 pour indiquer qu'on ne va pas avancer
            else:
                print("[✓] Fin du recul, reprise de la course")
                self.en_phase_recul = False
                time.sleep(0.3)  # Petite pause avant de repartir
        
        # ÉTAPE 1 : Vérifier les obstacles critiques (arrêt d'urgence)
        if (distance1 and distance1 < self.DISTANCE_URGENCE) or \
           (distance2 and distance2 < self.DISTANCE_URGENCE) or \
           (distance3 and distance3 < self.DISTANCE_URGENCE):
            print("[🛑] Obstacle CRITIQUE détecté! Arrêt d'urgence immédiat!")
            self.arreter_urgence()
            return None
        
        # ÉTAPE 1.5 : Vérifier si on tape un mur trop proche
        if distance1 and distance1 < self.DISTANCE_MUR_PROCHE:
            print(f"[💥] Mur détecté trop proche ({distance1:.1f}cm)! Recul + redirection...")
            self.en_phase_recul = True
            self.temps_recul_debut = time.time()
            # Inverser la direction du servo avant de reculer
            self.controleur.obtenir_servo().positionner(self.ANGLE_TOUT_DROIT)
            return 0
        
        # ÉTAPE 2 : Évaluer les obstacles présents
        vitesse_moteur = self.VITESSE_RAPIDE
        angle_servo = self.ANGLE_TOUT_DROIT
        
        # Obstacle devant = PRIORITÉ MAXIMALE
        if distance1 and distance1 < self.DISTANCE_OBSTACLE_DEVANT:
            # Obstacle proche devant → freinage fort + tourner
            if distance1 < 12:
                vitesse_moteur = self.VITESSE_FREINAGE
                print(f"[⚠️] Obstacle TRÈS PROCHE devant ({distance1:.1f}cm) → Freinage FORT")
            else:
                vitesse_moteur = self.VITESSE_RALENTI
                print(f"[⚠️] Obstacle devant ({distance1:.1f}cm) → Ralentir")
            
            # ÉTAPE 3 : Choisir la meilleure direction pour contourner
            angle_servo = self._choisir_meilleure_direction(distance2, distance3)
            
            if angle_servo == self.ANGLE_GAUCHE:
                print(f"    → Tourner à GAUCHE")
            elif angle_servo == self.ANGLE_DROITE:
                print(f"    → Tourner à DROITE")
        
        # Pas d'obstacle devant, vérifier les côtés
        else:
            # Obstacle à droite, mais on est déjà en train de tourner à droite
            if distance2 and distance2 < self.DISTANCE_OBSTACLE_COTE and self.derniere_direction == self.ANGLE_DROITE:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_DROITE # Maintenir la direction
                print(f"[✓] Obstacle à DROITE ({distance2:.1f}cm) mais virage à droite en cours → Maintien de la trajectoire")
            # Obstacle à gauche, mais on est déjà en train de tourner à gauche
            elif distance3 and distance3 < self.DISTANCE_OBSTACLE_COTE and self.derniere_direction == self.ANGLE_GAUCHE:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_GAUCHE # Maintenir la direction
                print(f"[✓] Obstacle à GAUCHE ({distance3:.1f}cm) mais virage à gauche en cours → Maintien de la trajectoire")
            # Obstacle à droite (cas standard)
            elif distance2 and distance2 < self.DISTANCE_OBSTACLE_COTE:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_GAUCHE
                print(f"[⚠️] Obstacle à DROITE ({distance2:.1f}cm) → Ralentir + Tourner à gauche")
            
            # Obstacle à gauche (cas standard)
            elif distance3 and distance3 < self.DISTANCE_OBSTACLE_COTE:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_DROITE
                print(f"[⚠️] Obstacle à GAUCHE ({distance3:.1f}cm) → Ralentir + Tourner à droite")
            
            # Pas d'obstacle
            else:
                vitesse_moteur = self.VITESSE_RAPIDE
                angle_servo = self.ANGLE_TOUT_DROIT
                print("[✓] Aucun obstacle → Vitesse maximale, direction centrée")
        
        # Appliquer l'angle au servo et mémoriser la direction
        if self.controleur:
            self.controleur.obtenir_servo().positionner(angle_servo)
        self.derniere_direction = angle_servo
        
        return vitesse_moteur
    
    def _choisir_meilleure_direction(self, distance_droite, distance_gauche):
        """
        Choisir la meilleure direction pour contourner un obstacle devant
        Retourne l'angle à appliquer au servo
        """
        # Si gauche est significativement plus libre que droite → tourner gauche
        if distance_gauche and distance_droite:
            if distance_gauche > distance_droite + 22:  # Seuil de 22cm de différence
                return self.ANGLE_GAUCHE
            elif distance_droite > distance_gauche - 23:
                return self.ANGLE_DROITE
        
        # Si une seule direction est libre
        if distance_gauche and distance_gauche > self.DISTANCE_OBSTACLE_COTE:
            return self.ANGLE_GAUCHE 
        if distance_droite and distance_droite > self.DISTANCE_OBSTACLE_COTE:
            return self.ANGLE_DROITE
        
        # Par défaut, continuer tout droit
        return self.ANGLE_TOUT_DROIT
    
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
                self.controleur.obtenir_servo().positionner(90)  # Centrer la direction
        except Exception as e:
            print(f"[✗] Erreur lors de l'arrêt d'urgence: {e}")

__name__ = "__main__"