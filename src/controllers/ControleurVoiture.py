"""
Contrôleur principal de la voiture 
Orchestrateur qui gère les capteurs et actionneurs

"""

import time
import sys
import os
import threading
import RPi.GPIO as GPIO
import Adafruit_PCA9685

# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports des composants matériel
from materiel.actionneurs.PiloteMoteur_L298N import PiloteMoteur_L298N
from materiel.actionneurs.PiloteServo_PCA9685 import ServoDirectionPCA
from materiel.capteurs.CapteurUltrason import CapteurUltrason
from materiel.capteurs.CapteurCouleur import CapteurCouleur
from materiel.capteurs.DetecteurLigneArrivee_IR import DetecteurLigneArrivee
from materiel.energie.Telemetrie_INA219 import Telemetrie_INA219
from models.SystemData import Data

from controllers.GestionSecurite import GestionSecurite
from views.web_server import app as flask_app


class ControleurVoiture:
    """Contrôleur principal de la voiture autonome"""
    
    def __init__(self):
        """Initialiser tous les composants"""
        self.pca = None
        self.moteur1 = None
        self.moteur2 = None
        self.servo = None
        self.capteur_couleur = None
        self.capteur_ultrason1 = None
        self.capteur_ultrason2 = None
        self.capteur_ultrason3 = None
        self.detecteur_arrivee = None
        self.telemetrie = None
        self.data = Data()
        self.en_marche = False  # Flag pour savoir si la voiture est en mouvement
        
        self._initialiser_composants()
        
        self.gestion_securite = GestionSecurite(controleur=self)
    
    def _initialiser_composants(self):
        """Initialiser les capteurs et actionneurs"""
        try:
            print("[*] Initialisation des composants...")
            self.data.ajouter_log_info("Initialisation des composants")
            
            # Initialiser le PCA9685 pour le PWM
            self.pca = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
            self.pca.set_pwm_freq(50)
            
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
                canal=0, pca=self.pca
            )
            
            # Initialiser les capteurs
            self.capteur_ultrason1 = CapteurUltrason(pin_trigger=6, pin_echo=5) #devant 
            self.capteur_ultrason2 = CapteurUltrason(pin_trigger=26, pin_echo=19) #droite
            self.capteur_ultrason3 = CapteurUltrason(pin_trigger=11, pin_echo=9) #gauche
            

            self.capteur_couleur = CapteurCouleur(adresse_i2c=0x29)
            self.capteur_couleur.initialiser()
            self.detecteur_arrivee = DetecteurLigneArrivee(pin_capteur=20)
            
            # Initialiser la télémétrie
            self.telemetrie = Telemetrie_INA219(adresse_i2c=0x44)
            
            print("[✓] Composants initialisés avec succès")
            self.data.ajouter_log_info("Composants initialisés avec succès")
        except Exception as e:
            print(f"[✗] Erreur lors de l'initialisation: {e}")
            self.data.ajouter_log_erreur(f"Erreur lors de l'initialisation: {e}")
            chemin = self.data.generer_log()
            print(f"[📄] Logs sauvegardés dans : {chemin}")
            self.gestion_securite.arreter_urgence()
            sys.exit(1)
    

    def run(self):
        """Boucle principale de contrôle"""
        try:
            print("[*] Démarrage de la boucle principale...")
            self.data.ajouter_log_info("Démarrage de la boucle principale")
            
            while True:
                # Lire les capteurs avec gestion d'erreur pour les ultrasonsécurité
                try:
                    distance1 = self.capteur_ultrason1.mesurer_distance() if self.capteur_ultrason1 else None
                except (TimeoutError, ValueError):
                    distance1 = 400  # Pas d'objet détecté = loin
                
                try:
                    distance2 = self.capteur_ultrason2.mesurer_distance() if self.capteur_ultrason2 else None
                except (TimeoutError, ValueError):
                    distance2 = 400  # Pas d'objet détecté = loin
                
                try:
                    distance3 = self.capteur_ultrason3.mesurer_distance() if self.capteur_ultrason3 else None
                except (TimeoutError, ValueError):
                    distance3 = 400  # Pas d'objet détecté = loin
                
                arrivee_detectee = self.detecteur_arrivee.est_sur_ligne_arrivee() if self.detecteur_arrivee else False
                
                tension = self.telemetrie.lire_tension() if self.telemetrie else None
                courant = self.telemetrie.lire_courant() if self.telemetrie else None

                if tension is not None and courant is not None:
                    print(f"[📊] Télémétrie - Tension: {tension:.2f} V, Courant: {courant:.2f} mA")
                    self.data.ajouter_log_info(f"Télémétrie - Tension: {tension:.2f} V, Courant: {courant:.2f} mA")
                else:
                    print("[📊] Télémétrie - Données non disponibles")
                    self.data.ajouter_log_erreur("Télémétrie indisponible")

                self.data.ajouter_log_info(f"Distances - devant: {distance1}, droite: {distance2}, gauche: {distance3}")
                
                # ÉTAPE 1: Vérifier la ligne d'arrivée en priorité
                if arrivee_detectee:
                    print("[!] Ligne d'arrivée détectée! Course terminée!")
                    self.data.ajouter_log_info("Ligne d'arrivée détectée - fin de course")
                    self.moteur1.arreter()
                    self.moteur2.arreter()
                    break
                
                # ÉTAPE 2: Si pas encore en marche, attendre le feu vert
                if not self.en_marche:
                    rouge, vert, bleu, clair = self.capteur_couleur.lire_valeurs_brutes() if self.capteur_couleur else (0, 0, 0, 0)
                    couleur_dominante = self.capteur_couleur.detecter_couleur_dominante(rouge, vert, bleu, clair) if self.capteur_couleur else "inconnu"
                    print(f"[🎨] Capteur Couleur - R: {rouge}, G: {vert}, B: {bleu}, C: {clair}")
                    print(f"[🎨] Capteur Couleur - Couleur dominante: {couleur_dominante}")
                    self.data.ajouter_log_info(f"Capteur couleur - R:{rouge} G:{vert} B:{bleu} C:{clair} dominante:{couleur_dominante}")

                    # Vérifier la sécurité du feu
                    if not self.gestion_securite.verifier_securite_feu(couleur_dominante):
                        self.gestion_securite.arreter_urgence()
                        print("[🛑] Arrêt d'urgence déclenché en raison du feu de signalisation!")
                        self.data.ajouter_log_erreur("Arrêt d'urgence déclenché (feu/capteur couleur)")
                        break
                    
                    # Si feu vert, on démarre la course
                    if couleur_dominante == "vert":
                        print("[🟢] Feu vert détecté → Démarrage de la course!")
                        self.data.ajouter_log_info("Feu vert détecté - démarrage de la course")
                        self.en_marche = True
                    else:
                        # En attente du feu vert
                        print(f"[🔴] En attente du feu vert (capteur: {couleur_dominante})")
                        self.moteur1.arreter()
                        self.moteur2.arreter()
                        time.sleep(0.1)
                        continue
                
                # ÉTAPE 3: Une fois en marche, gérer les obstacles et avancer
                if self.en_marche:
                    # Vérifier la sécurité des obstacles
                    vitesse_moteur = self.gestion_securite.verifier_securite_distance(distance1, distance2, distance3)
                    
                    if vitesse_moteur is None:
                        self.data.ajouter_log_erreur("Arrêt d'urgence déclenché (obstacle critique)")
                        break

                    if vitesse_moteur is not None and vitesse_moteur > 0:
                        self.moteur1.avancer(vitesse=vitesse_moteur)
                        self.moteur2.avancer(vitesse=vitesse_moteur)

                        niveau_batterie = int(tension) if tension is not None else 0
                        self.data.actualise(vitesse=vitesse_moteur, batterie=niveau_batterie, angle_roue=0)
                        self.data.ajouter_log_info(f"Moteurs en marche - vitesse: {vitesse_moteur}%")

                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
            self.data.ajouter_log_info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"[✗] Erreur: {e}")
            self.data.ajouter_log_erreur(f"Erreur dans la boucle principale: {e}")
        finally:
            self.gestion_securite.arreter_urgence()
            self.data.ajouter_log_info("Arrêt d'urgence final et fin de session")
            chemin = self.data.generer_log()
            print(f"[📄] Logs sauvegardés dans : {chemin}")

def main():
    """Point d'entrée du programme"""
    controleur = ControleurVoiture()
    controleur.run()


if __name__ == "__main__":
    main()
