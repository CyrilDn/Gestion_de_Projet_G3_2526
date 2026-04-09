"""
Contrôleur principal de la voiture 
Orchestrateur qui gère les capteurs et actionneurs

"""

import time
import sys

# Imports des composants matériel
from src.materiel.actionneurs.PiloteMoteur_L298N import PiloteMoteur_L298N
from src.materiel.actionneurs.PiloteServo_PCA9685 import ServoDirectionPCA
from src.materiel.capteurs.CapteurUltrason import CapteurUltrason
from src.materiel.capteurs.CapteurCouleur import CapteurCouleur
from src.materiel.capteurs.DetecteurLigneArrivee_IR import DetecteurLigneArrivee
from src.materiel.energie.Telemetrie_INA219 import Telemetrie_INA219


class ControleurVoiture:
    """Contrôleur principal de la voiture autonome"""
    
    def __init__(self):
        """Initialiser tous les composants"""
        self.moteur = None
        self.servo = None
        self.capteur_couleur = None
        self.capteur_ultrason = None
        self.detecteur_arrivee = None
        self.telemetrie = None
        
        self._initialiser_composants()
    
    def _initialiser_composants(self):
        """Initialiser les capteurs et actionneurs"""
        try:
            print("[*] Initialisation des composants...")
            
            # Initialiser le moteur DC
            self.moteur = PiloteMoteur_L298N(
                pin_in1=23, pin_in2=18, pin_pwm=5
            )
            self.moteur = PiloteMoteur_L298N(
                pin_in1=27, pin_in2=22, pin_pwm=4
            )
            
            # Initialiser le servo
            self.servo = ServoDirectionPCA(
                channel=0
            )
            
            # Initialiser les capteurs
            self.capteur_ultrason = CapteurUltrason()
            self.capteur_couleur = CapteurCouleur()
            self.detecteur_arrivee = DetecteurLigneArrivee()
            
            # Initialiser la télémétrie
            self.telemetrie = Telemetrie_INA219()
            
            print("[✓] Composants initialisés avec succès")
        except Exception as e:
            print(f"[✗] Erreur lors de l'initialisation: {e}")
            self.arreter_urgence()
            sys.exit(1)
    
    def run(self):
        """Boucle principale de contrôle"""
        try:
            print("[*] Démarrage de la boucle principale...")
            
            while True:
                # Lire les capteurs
                distance = self.capteur_ultrason.mesurer_distance() if self.capteur_ultrason else None
                arrivee_detectee = self.detecteur_arrivee.detecter() if self.detecteur_arrivee else False
                
                # Logique de contrôle
                if arrivee_detectee:
                    print("[!] Ligne d'arrivée détectée!")
                    self.moteur.arreter()
                    break
                
                if distance and distance < 20:
                    print(f"[!] Obstacle détecté à {distance}cm")
                    # Tourner à droite pour éviter l'obstacle
                    self.servo.tourner_droite()
                    self.moteur.avancer(vitesse=50)
                else:
                    self.moteur.avancer(vitesse=60)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"[✗] Erreur: {e}")
        finally:
            self.arreter_urgence()
    
    def arreter_urgence(self):
        """Arrêt d'urgence et nettoyage des ressources"""
        print("[*] Arrêt de la voiture...")
        
        try:
            if self.moteur:
                self.moteur.arreter()
                self.moteur.nettoyer()
        except Exception as e:
            print(f"[✗] Erreur lors du nettoyage moteur: {e}")
        
        print("[✓] Arrêt complet")


def main():
    """Point d'entrée du programme"""
    controleur = ControleurVoiture()
    controleur.run()


if __name__ == "__main__":
    main()
