"""
Contrôleur principal de la voiture 
Orchestrateur qui gère les capteurs et actionneurs

"""

import time
import sys
import os
import RPi.GPIO as GPIO
import board
import busio
from adafruit_pca9685 import PCA9685

# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports des composants matériel
from materiel.actionneurs.PiloteMoteur_L298N import PiloteMoteur_L298N
from materiel.actionneurs.PiloteServo_PCA9685 import ServoDirectionPCA
from materiel.capteurs.CapteurUltrason import CapteurUltrason
from materiel.capteurs.CapteurCouleur import CapteurCouleur
from materiel.capteurs.DetecteurLigneArrivee_IR import DetecteurLigneArrivee
from materiel.energie.Telemetrie_INA219 import Telemetrie_INA219


class ControleurVoiture:
    """Contrôleur principal de la voiture autonome"""
    
    def __init__(self):
        """Initialiser tous les composants"""
        self.pca = None
        self.moteur1 = None
        self.moteur2 = None
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
            
            # Initialiser le PCA9685 pour le PWM
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(i2c)
            self.pca.frequency = 50
            
            # Initialiser GPIO
            GPIO.setmode(GPIO.BCM)
            
            # Initialiser les deux moteurs DC avec le PCA9685
            self.moteur1 = PiloteMoteur_L298N(
                pin_in1=23, pin_in2=18, canal_pwm=5, pca=self.pca
            )
            self.moteur2 = PiloteMoteur_L298N(
                pin_in1=27, pin_in2=22, canal_pwm=4, pca=self.pca
            )
            
            # Initialiser le servo
            self.servo = ServoDirectionPCA(
                canal=0
            )
            
            # Initialiser les capteurs
            self.capteur_ultrason = CapteurUltrason(pin_trigger=11, pin_echo=9) #gauche
            self.capteur_ultrason = CapteurUltrason(pin_trigger=6, pin_echo=5) #devant 
            self.capteur_ultrason = CapteurUltrason(pin_trigger=26, pin_echo=19) #droite
            self.capteur_couleur = CapteurCouleur(adresse_i2c=0x29)
            self.detecteur_arrivee = DetecteurLigneArrivee(pin_capteur=20)
            
            # Initialiser la télémétrie
            self.telemetrie = Telemetrie_INA219(adresse_i2c=0x40)
            
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
                arrivee_detectee = self.detecteur_arrivee.est_sur_ligne_arrivee() if self.detecteur_arrivee else False
                
                # Logique de contrôle
                if arrivee_detectee:
                    print("[!] Ligne d'arrivée détectée!")
                    self.moteur.arreter()
                    break
                
                if distance and distance < 20:
                    print(f"[!] Obstacle détecté à {distance}cm")
                    # Tourner à droite pour éviter l'obstacle
                    self.servo.tourner_droite()
                    self.moteur1.avancer(vitesse=50)
                    self.moteur2.avancer(vitesse=50)
                else:
                    self.moteur1.avancer(vitesse=60)
                    self.moteur2.avancer(vitesse=60)
                
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
            if self.moteur1:
                self.moteur1.arreter()
                self.moteur1.nettoyer()
            if self.moteur2:
                self.moteur2.arreter()
                self.moteur2.nettoyer()
        except Exception as e:
            print(f"[✗] Erreur lors du nettoyage moteur: {e}")
        
        print("[✓] Arrêt complet")


def main():
    """Point d'entrée du programme"""
    controleur = ControleurVoiture()
    controleur.run()


if __name__ == "__main__":
    main()
