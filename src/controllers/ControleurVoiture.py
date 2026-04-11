"""
Contrôleur principal de la voiture
Orchestrateur qui gère les capteurs et actionneurs

"""

import time
import sys
import os
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


class ControleurVoiture:
    """Contrôleur principal de la voiture autonome"""

    def __init__(self):
        """Initialiser tous les composants"""
        self._pca = None
        self._moteur1 = None
        self._moteur2 = None
        self._servo = None
        self._capteur_couleur = None
        self._capteur_ultrason1 = None
        self._capteur_ultrason2 = None
        self._capteur_ultrason3 = None
        self._detecteur_arrivee = None
        self._telemetrie = None
        self._data = Data()
        self._en_marche = False
        self._compteur_tours = 0
        self._dernier_passage_arrivee = 0
        
        self._initialiser_composants()

        self._gestion_securite = GestionSecurite(controleur=self)

    def _initialiser_composants(self):
        """Initialiser les capteurs et actionneurs"""
        try:
            print("[*] Initialisation des composants...")
            self._data.ajouter_log_info("Initialisation des composants")

            # Initialiser le PCA9685 pour le PWM
            self._pca = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
            self._pca.set_pwm_freq(50)
            
            # Initialiser GPIO
            GPIO.setmode(GPIO.BCM)

            # Initialiser les deux moteurs DC avec le PCA9685
            self._moteur1 = PiloteMoteur_L298N(
                pin_in1=23, pin_in2=18, canal_pwm=5, pca=self._pca
            )
            self._moteur2 = PiloteMoteur_L298N(
                pin_in1=27, pin_in2=22, canal_pwm=4, pca=self._pca
            )

            # Initialiser le servo
            self._servo = ServoDirectionPCA(
                canal=0, pca=self._pca
            )
            
            # Initialiser les capteurs
            self._capteur_ultrason1 = CapteurUltrason(pin_trigger=6, pin_echo=5) #devant 
            self._capteur_ultrason2 = CapteurUltrason(pin_trigger=26, pin_echo=19) #droite
            self._capteur_ultrason3 = CapteurUltrason(pin_trigger=11, pin_echo=9) #gauche
            

            self._capteur_couleur = CapteurCouleur(adresse_i2c=0x29)
            self._capteur_couleur.initialiser()
            self._detecteur_arrivee = DetecteurLigneArrivee(pin_capteur=20)
            
            # Initialiser la télémétrie
            self._telemetrie = Telemetrie_INA219(adresse_i2c=0x44)
            
            print("[✓] Composants initialisés avec succès")
            self._data.ajouter_log_info("Composants initialisés avec succès")
        except Exception as e:
            print(f"[✗] Erreur lors de l'initialisation: {e}")
            self._data.ajouter_log_erreur(f"Erreur lors de l'initialisation: {e}")
            chemin = self._data.generer_log()
            print(f"[📄] Logs sauvegardés dans : {chemin}")
            self._gestion_securite.arreter_urgence()
            sys.exit(1)
    
    # ===== MÉTHODES PUBLIQUES POUR LE CONTRÔLE DE LA VOITURE =====
    
    def arreter_moteurs(self):
        """Arrêter les deux moteurs"""
        self._moteur1.arreter()
        self._moteur2.arreter()
    
    def avancer_moteurs(self, vitesse):
        """Faire avancer les moteurs à une vitesse donnée (0-100)"""
        self._moteur1.avancer(vitesse=vitesse)
        self._moteur2.avancer(vitesse=vitesse)

    def reculer_moteurs(self, vitesse):
        """Faire reculer les moteurs à une vitesse donnée (0-100)"""
        self._moteur1.reculer(vitesse=vitesse)
        self._moteur2.reculer(vitesse=vitesse)
    
    def obtenir_etat_marche(self):
        """Retourner si la voiture est actuellement en marche"""
        return self._en_marche
    
    def definir_etat_marche(self, etat):
        """Définir l'état de marche de la voiture"""
        self._en_marche = etat
    
    def obtenir_distance_ultrason(self, position):
        """Obtenir la distance d'un capteur ultrason (avant/droite/gauche)"""
        if position == "avant":
            return self._capteur_ultrason1.mesurer_distance() if self._capteur_ultrason1 else None
        elif position == "droite":
            return self._capteur_ultrason2.mesurer_distance() if self._capteur_ultrason2 else None
        elif position == "gauche":
            return self._capteur_ultrason3.mesurer_distance() if self._capteur_ultrason3 else None
        return None
    
    def obtenir_couleur(self):
        """Retourner la couleur dominante détectée par le capteur couleur"""
        rouge, vert, bleu, clair = self._capteur_couleur.lire_valeurs_brutes() if self._capteur_couleur else (0, 0, 0, 0)
        couleur_dominante = self._capteur_couleur.detecter_couleur_dominante(rouge, vert, bleu, clair) if self._capteur_couleur else "inconnu"
        return couleur_dominante
    
    def obtenir_telemetrie(self):
        """Retourner la tension et le courant actuels"""
        tension = self._telemetrie.lire_tension() if self._telemetrie else None
        courant = self._telemetrie.lire_courant() if self._telemetrie else None
        return tension, courant
    
    def est_sur_ligne_arrivee(self):
        """Vérifier si la voiture est sur la ligne d'arrivée"""
        return self._detecteur_arrivee.est_sur_ligne_arrivee() if self._detecteur_arrivee else False
    
    def obtenir_servo(self):
        """Retourner le servo pour le contrôle de la direction"""
        return self._servo
    
    # ===== ========================== =====



    def lire_capteurs(self):
        """Lire tous les capteurs et retourner un dictionnaire avec les données"""
        # Lire les capteurs avec gestion d'erreur pour les ultrasons
        try:
            distance1 = self._capteur_ultrason1.mesurer_distance() if self._capteur_ultrason1 else None
        except (TimeoutError, ValueError):
            distance1 = 400  # Pas d'objet détecté = loin
        try:
            distance2 = self._capteur_ultrason2.mesurer_distance() if self._capteur_ultrason2 else None
        except (TimeoutError, ValueError):
            distance2 = 400  # Pas d'objet détecté = loin
        try:
            distance3 = self._capteur_ultrason3.mesurer_distance() if self._capteur_ultrason3 else None
        except (TimeoutError, ValueError):
            distance3 = 400  # Pas d'objet détecté = loin
        
        arrivee_detectee = self._detecteur_arrivee.est_sur_ligne_arrivee() if self._detecteur_arrivee else False
        
        tension = self._telemetrie.lire_tension() if self._telemetrie else None
        courant = self._telemetrie.lire_courant() if self._telemetrie else None

        if tension is not None and courant is not None:
            print(f"[📊] Télémétrie - Tension: {tension:.2f} V, Courant: {courant:.2f} mA")
            self._data.ajouter_log_info(f"Télémétrie - Tension: {tension:.2f} V, Courant: {courant:.2f} mA")
        else:
            print("[📊] Télémétrie - Données non disponibles")
            self._data.ajouter_log_erreur("Télémétrie indisponible")

        self._data.ajouter_log_info(f"Distances - devant: {distance1}, droite: {distance2}, gauche: {distance3}")
        
        return {
            'distance_avant': distance1,
            'distance_droite': distance2,
            'distance_gauche': distance3,
            'arrivee_detectee': arrivee_detectee,
            'tension': tension,
            'courant': courant
        }

    def attendre_feu_vert(self):
        """Attendre le feu vert avant de démarrer la course"""
        while True:
            rouge, vert, bleu, clair = self._capteur_couleur.lire_valeurs_brutes() if self._capteur_couleur else (0, 0, 0, 0)
            couleur_dominante = self._capteur_couleur.detecter_couleur_dominante(rouge, vert, bleu, clair) if self._capteur_couleur else "inconnu"
            print(f"[🎨] Capteur Couleur - R: {rouge}, G: {vert}, B: {bleu}, C: {clair}")
            print(f"[🎨] Capteur Couleur - Couleur dominante: {couleur_dominante}")
            self._data.ajouter_log_info(f"Capteur couleur - R:{rouge} G:{vert} B:{bleu} C:{clair} dominante:{couleur_dominante}")

            if couleur_dominante == "vert":
                print("[🟢] Feu vert détecté → Démarrage de la course!")
                self._data.ajouter_log_info("Feu vert détecté - démarrage de la course")
                return
            elif couleur_dominante == "aucune":
                print("[⚠️] Aucune couleur détectée, possible problème de capteur")
                self._gestion_securite.arreter_urgence()
                print("[🛑] Arrêt d'urgence déclenché en raison du feu de signalisation!")
                self._data.ajouter_log_erreur("Arrêt d'urgence déclenché (feu/capteur couleur)")
                sys.exit(1)
            else:
                print(f"[🔴] En attente du feu vert (capteur: {couleur_dominante})")
                self.arreter_moteurs()
                time.sleep(0.1)

    def run(self, nombre_tour=3, resume=False):
        """Boucle principale de contrôle"""

        try:
            print("[*] Démarrage de la boucle principale...")
            self._data.ajouter_log_info("Démarrage de la boucle principale")

            # Si c'est un redémarrage, récupérer les tours déjà effectués
            if resume:
                import json
                tours_file = os.path.join(os.path.dirname(__file__), "..", "models", "tours.json")
                if os.path.exists(tours_file):
                    with open(tours_file, 'r', encoding='utf-8') as f:
                        tours_data = json.load(f)
                    self._compteur_tours = tours_data.get('nombre_actuel', 0)
                    print(f"[*] Redémarrage - Tours effectués: {self._compteur_tours}")
                    self._data.ajouter_log_info(f"Redémarrage - Tours effectués: {self._compteur_tours}")
                    self._en_marche = True  # Lancer directement sans attendre le feu vert
                else:
                    print("[!] Fichier tours.json non trouvé pour le redémarrage")
                    self._data.ajouter_log_erreur("Fichier tours.json non trouvé pour le redémarrage")

            # Sauvegarder le nombre total de tours au démarrage
            self._data.actualiser_nombre_tours(self._compteur_tours, nombre_tour)

            while True:
                # Lire tous les capteurs
                capteurs = self.lire_capteurs()
                distance1 = capteurs['distance_avant']
                distance2 = capteurs['distance_droite']
                distance3 = capteurs['distance_gauche']
                arrivee_detectee = capteurs['arrivee_detectee']
                tension = capteurs['tension']
                courant = capteurs['courant']
                
                # ÉTAPE 1: Vérifier la ligne d'arrivée en priorité
                if arrivee_detectee:
                    maintenant = time.time()
                    # Ignorer si on vient de passer (évite les double-détections)
                    if maintenant - self._dernier_passage_arrivee > 2:
                        self._dernier_passage_arrivee = maintenant
                        self._compteur_tours += 1
                        print(
                            f"Passage ligne arrivée — tour {self._compteur_tours}/{nombre_tour}"
                        )
                        self._data.ajouter_log_info(
                            f"Tour {self._compteur_tours}/{nombre_tour}"
                        )
                        self._data.actualiser_nombre_tours(self._compteur_tours, nombre_tour)


                        if self._compteur_tours >= nombre_tour:
                            print("Fin de course")
                            self._data.ajouter_log_info("Fin de la course !")
                            # Réinitialiser le JSON AVANT d'arrêter
                            self._data.actualiser_nombre_tours(0, 0)
                            self._moteur1.arreter()
                            self._moteur2.arreter()

                            break

                
                # ÉTAPE 2: Si pas encore en marche, attendre le feu vert
                if not self._en_marche:
                    self.attendre_feu_vert()
                    self._en_marche = True
                
                # ÉTAPE 3: Une fois en marche, gérer les obstacles et avancer
                if self._en_marche:
                    # Vérifier la sécurité des obstacles
                    vitesse_moteur = self._gestion_securite.verifier_securite_distance(
                        distance1, distance2, distance3
                    )

                    if vitesse_moteur is None:
                        self._data.ajouter_log_erreur(
                            "Arrêt d'urgence déclenché (obstacle critique)"
                        )
                        break

                    if vitesse_moteur is not None and vitesse_moteur > 0:
                        self.avancer_moteurs(vitesse=vitesse_moteur)

                        niveau_batterie = int(tension) if tension is not None else 0
                        self._data.actualise(
                            vitesse=vitesse_moteur,
                            batterie=niveau_batterie,
                            angle_roue=0,
                        )
                        self._data.ajouter_log_info(
                            f"Moteurs en marche - vitesse: {vitesse_moteur}%"
                        )

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
            self._data.ajouter_log_info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"[✗] Erreur: {e}")
            self._data.ajouter_log_erreur(f"Erreur dans la boucle principale: {e}")
        finally:
            self._gestion_securite.arreter_urgence()
            self._data.ajouter_log_info("Arrêt d'urgence final et fin de session")
            chemin = self._data.generer_log()
            print(f"[📄] Logs sauvegardés dans : {chemin}")


def main():
    """Point d'entrée du programme"""
    import json

    # Récupérer les arguments
    nombre_tours = 3  # Par défaut
    resume = False

    if len(sys.argv) > 1:
        try:
            nombre_tours = int(sys.argv[1])
        except ValueError:
            nombre_tours = 3

    if '--resume' in sys.argv:
        resume = True

    controleur = ControleurVoiture()
    controleur.run(nombre_tours, resume)

if __name__ == "__main__":
    main()
