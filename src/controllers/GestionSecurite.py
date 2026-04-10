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
        
        # Trouver l'obstacle le plus critique (le plus proche)
        obstacles = []
        if distance1 and distance1 < 20:
            obstacles.append(("devant", distance1, 90))
        if distance2 and distance2 < 10:
            obstacles.append(("droite", distance2, 45))
        if distance3 and distance3 < 10:
            obstacles.append(("gauche", distance3, 135))
        
        if obstacles:
            # Trier par distance (le plus proche en premier)
            obstacle_critique = min(obstacles, key=lambda x: x[1])
            position, distance, angle = obstacle_critique
            
            if distance < 10:
                vitesse_moteur = 31
            else:
                vitesse_moteur = 50
            
            if self.controleur and self.controleur.servo:
                self.controleur.servo.positionner(angle)
            print(f"[!] Obstacle {position} ({distance:.1f}cm) → Vitesse: {vitesse_moteur}, Angle: {angle}°")
        else:
            # Pas d'obstacle
            vitesse_moteur = 80
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