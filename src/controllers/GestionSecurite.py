import time

class GestionSecurite:
    def __init__(self, controleur):
        """Initialiser les paramètres de sécurité"""
        self.controleur = controleur
        self.distance_securite = 7  # Distance minimale en cm pour la sécurité (arrêt d'urgence)

    def verifier_securite_distance(self, distance1, distance2, distance3):
        """
        Vérifier les conditions de sécurité ET traiter les obstacles
        Retourne None si arrêt d'urgence déclenché, sinon retourne la vitesse (0-80)
        """
        # Vérification de sécurité distance critique
        if distance1 and distance1 < self.distance_securite:
            print("[!] Obstacle critique détecté devant! Arrêt d'urgence.")
            self.arreter_urgence()
            print("[🛑] Arrêt d'urgence déclenché!")
            return None
        if distance2 and distance2 < self.distance_securite:
            print("[!] Obstacle critique détecté à droite! Arrêt d'urgence.")
            self.arreter_urgence()
            print("[🛑] Arrêt d'urgence déclenché!")
            return None
        if distance3 and distance3 < self.distance_securite:
            print("[!] Obstacle critique détecté à gauche! Arrêt d'urgence.")
            self.arreter_urgence()
            print("[🛑] Arrêt d'urgence déclenché!")
            return None
        
        vitesse_moteur = 80
        
        # PRIORITÉ 1 : Vérifier l'obstacle devant en premier
        if distance1 and distance1 < 40:  # ← Augmenté de 20 à 40cm
            angle_virage = 90  # Par défaut : tout droit
        
            if distance3 and distance3 > distance2:  # Gauche libre
                angle_virage = 113  # Tourner à gauche
                direction = "gauche"
            else:  # Droite libre
                angle_virage = 67 # Tourner à droite
                direction = "droite"
            
            if distance1 < 15:
                vitesse_moteur = 31
                print(f"[!] Obstacle devant ({distance1:.1f}cm) → Freinage FORT + Tourne {direction}")
            else:
                vitesse_moteur = 50
                print(f"[!] Obstacle devant ({distance1:.1f}cm) → Freinage modéré + Tourne {direction}")
            
            if self.controleur and self.controleur.servo:
                self.controleur.servo.positionner(angle_virage)
        else:
            # PRIORITÉ 2 : Sinon, chercher l'obstacle le plus critique
            obstacles = []
            if distance2 and distance2 < 25:  # ← Augmenté de 10 à 25cm
                obstacles.append(("droite", distance2, 67))
            if distance3 and distance3 < 25:  # ← Augmenté de 10 à 25cm
                obstacles.append(("gauche", distance3, 113))
            
            if obstacles:
                obstacle_critique = min(obstacles, key=lambda x: x[1])
                position, distance, angle = obstacle_critique
                
                vitesse_moteur = 31
                if self.controleur and self.controleur.servo:
                    self.controleur.servo.positionner(angle)
                print(f"[!] Obstacle {position} ({distance:.1f}cm) → Vitesse: {vitesse_moteur}, Angle: {angle}°")
            else:
                # Pas d'obstacle
                vitesse_moteur = 35
                if self.controleur and self.controleur.servo:
                    self.controleur.servo.positionner(90)
                print("[✓] Aucun obstacle, vitesse normale, direction centrée")
        
        return vitesse_moteur
    
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
                if self.controleur.moteur1:
                    self.controleur.moteur1.arreter()
                    self.controleur.servo.positionner(90)  # Centrer la direction
                if self.controleur.moteur2:
                    self.controleur.moteur2.arreter()
                    self.controleur.servo.positionner(90)  # Centrer la direction
        except Exception as e:
            print(f"[✗] Erreur lors de l'arrêt d'urgence: {e}")

__name__ = "__main__"