import time

class GestionSecurite:
    # Constantes de sécurité
    DISTANCE_URGENCE = 0 # Distance critique (arrêt immédiat)
    DISTANCE_OBSTACLE_DEVANT = 20 # Obstacle devant détecté
    DISTANCE_OBSTACLE_COTE = 15 # Obstacle sur les côtés
    
    # Constantes de vitesse
    VITESSE_RAPIDE = 70 # Pas d'obstacle
    VITESSE_NORMALE = 50 # Obstacle éloigné
    VITESSE_RALENTI = 40 # Obstacle modéré
    VITESSE_FREINAGE = 25 # Obstacle proche
    
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
        Vérifier les conditions de sécurité ET traiter les obstacles
        Retourne la vitesse (0-80)
        """
        
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
            # Obstacle à droite
            if distance2 and distance2 < self.DISTANCE_OBSTACLE_COTE:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_GAUCHE
                print(f"[⚠️] Obstacle à DROITE ({distance2:.1f}cm) → Ralentir + Tourner à gauche")
            
            # Obstacle à gauche
            elif distance3 and distance3 < self.DISTANCE_OBSTACLE_COTE:
                vitesse_moteur = self.VITESSE_RALENTI
                angle_servo = self.ANGLE_DROITE
                print(f"[⚠️] Obstacle à GAUCHE ({distance3:.1f}cm) → Ralentir + Tourner à droite")
            
            # Pas d'obstacle
            else:
                vitesse_moteur = self.VITESSE_RAPIDE
                angle_servo = self.ANGLE_TOUT_DROIT
                print("[✓] Aucun obstacle → Vitesse maximale, direction centrée")
        
        # Appliquer l'angle au servo
        if self.controleur:
            self.controleur.obtenir_servo().positionner(angle_servo)
        
        return vitesse_moteur
    
    def _choisir_meilleure_direction(self, distance_droite, distance_gauche):
        """
        Choisir la meilleure direction pour contourner un obstacle devant
        Tourner VERS le capteur ayant la plus petite valeur (inverse de la marche arrière)
        Retourne l'angle à appliquer au servo
        """
        # Si droite est plus proche que gauche → tourner à GAUCHE (sens opposé)
        if distance_gauche and distance_droite:
            if distance_droite < distance_gauche - 5:  # Seuil de 5cm de différence
                return self.ANGLE_GAUCHE
            elif distance_gauche < distance_droite - 5:
                return self.ANGLE_DROITE
        
        # Si une seule direction est disponible
        if distance_gauche and not distance_droite:
            return self.ANGLE_GAUCHE
        if distance_droite and not distance_gauche:
            return self.ANGLE_DROITE
        
        # Par défaut, continuer tout droit
        return self.ANGLE_TOUT_DROIT
    
    def verifier_securite_feu(self, couleur_dominante):
        """Vérifier les conditions de sécurité liées au feu de signalisation"""
        if couleur_dominante == "aucune":
            print("[⚠️] Aucune couleur détectée, possible problème de capteur")
            return False
        return True
    
    def arreter_urgence(self):
        """Fonction dépréciée - conservée pour compatibilité"""
        pass

__name__ = "__main__"