import time


class GestionSecurite:
    def __init__(self, controleur=None):
        """Initialiser les paramètres de sécurité"""
        self.controleur = controleur
        self.distance_securite = 15 # Distance minimale en cm pour la sécurité

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
        
        # Gérer obstacle devant (distance1)
        if distance1 and distance1 < 20:
            vitesse_moteur = 31
            if self.controleur and self.controleur.servo:
                self.controleur.servo.positionner(90)
            print(f"[!] Obstacle devant ({distance1}cm) → Ralentir fortement")
        elif distance1 and distance1 < 40:
            vitesse_moteur = 50
            if self.controleur and self.controleur.servo:
                self.controleur.servo.positionner(90)
            print(f"[!] Obstacle devant ({distance1}cm) → Ralentir modérément")
        
        # Obstacle à droite
        elif distance2 and distance2 < 20:
            vitesse_moteur = 31
            if self.controleur and self.controleur.servo:
                self.controleur.servo.positionner(45)
            print(f"[!] Obstacle à droite ({distance2}cm) → Tourner à gauche + Ralentir")
        
        # Obstacle à gauche
        elif distance3 and distance3 < 20:
            vitesse_moteur = 31
            if self.controleur and self.controleur.servo:
                self.controleur.servo.positionner(135)
            print(f"[!] Obstacle à gauche ({distance3}cm) → Tourner à droite + Ralentir")
        
        # Pas d'obstacle
        else:
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
                if self.controleur.moteur2:
                    self.controleur.moteur2.arreter()
        except Exception as e:
            print(f"[✗] Erreur lors de l'arrêt d'urgence: {e}")

__name__ = "__main__"