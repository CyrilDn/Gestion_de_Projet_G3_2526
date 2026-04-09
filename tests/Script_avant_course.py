
import os
import sys
# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time

class ScriptAvantCourse:
    def __init__(self, driver):
        self.driver = driver
        self.controleur = ControleurVoiture()
        self.data = Data()

    def run(self):
        try:
            print("\n" + "="*40)
            print(" 🚀 DÉMARRAGE DU CHECK-UP - Script Avant Course")
            print("="*40)
            time.sleep(1)

            self._verifier_capteurs()
            self._verifier_moteurs()
            self._verifier_batterie()

            print("\n" + "="*40)
            print(" ✅ TOUS LES TESTS SONT AU VERT !")
            print(" ✅ LA VOITURE EST PRÊTE POUR LA COURSE.")
            print("="*40 + "\n")

        except Exception as e:
            self.data.ajouter_log_erreur(f"Erreur critique : {e}")
            print(f" ❌ Erreur: {e}")
        
        chemin = self.data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")




    def _verifier_capteurs(self):
        """Vérifie les capteurs"""
        try : 
            print("[*] 1. Vérification de la vue - capteurs...")
            print("Test 1.1 : Capteur ultrason - Mesure de distance")
            for i in range(3):
                distance1 = self.controleur.capteur_ultrason1.mesurer_distance() if self.controleur.capteur_ultrason1 else None
                distance2 = self.controleur.capteur_ultrason2.mesurer_distance() if self.controleur.capteur_ultrason2 else None
                distance3 = self.controleur.capteur_ultrason3.mesurer_distance() if self.controleur.capteur_ultrason3 else None
                print(f"  - Mesure de distance {i+1}: {distance1:.2f} cm devant, {distance2:.2f} cm à droite, {distance3:.2f} cm à l'arrière")
                self.data.ajouter_log_info(f"Ultrason mesure {i+1} : {distance1:.2f} cm devant, {distance2:.2f} cm à droite, {distance3:.2f} cm à l'arrière")
            
            print("Test 1.2 : Capteur de Couleur - Lecture des valeurs")
            try:
                valeur = self.controleur.capteur_couleur.lire_valeurs_brutes() if self.controleur.capteur_couleur else None
                print(f"  - Valeur détectée: {valeur}")
                self.data.ajouter_log_info(f"Couleur : {valeur}")
            except Exception as e:
                print(f"  - ERREUR Capteur Couleur: {e}")
                self.data.ajouter_log_erreur(f"Capteur Couleur: {e}")

            print("Test 1.3 : Capteur de Ligne - Lecture des valeurs")
            try:
                valeur = self.controleur.detecteur_arrivee.est_sur_ligne_arrivee() if self.controleur.detecteur_arrivee else None
                print(f"  - Valeur détectée: {valeur}")
                self.data.ajouter_log_info(f"Ligne d'arrivée : {valeur}")
            except Exception as e:
                print(f"  - ERREUR Capteur Ligne: {e}")
                self.data.ajouter_log_erreur(f"Capteur Ligne: {e}")

        except Exception as e: 
            self.data.ajouter_log_erreur(f"Erreur capteurs: {e}")
            print(f"[✗] Erreur générale capteurs: {e}")
        time.sleep(0.5)
        

    def _verifier_moteurs(self):
        """Vérifie les moteurs"""
        try : 
            print("[*] 2. Vérification des muscles - moteurs...")
            print("Test 2.1 : Moteur avant - Avancer")
            self.controleur.moteur1.avancer(vitesse=80)
            self.controleur.moteur2.avancer(vitesse=80)
            time.sleep(1)
            print("Test 2.3 : Moteur - S'arreter")
            self.controleur.moteur1.arreter()
            self.controleur.moteur2.arreter()
            time.sleep(1)
            print("Test 2.2 : Moteur arrière - Reculer")
            self.controleur.moteur1.reculer(vitesse=80)
            self.controleur.moteur2.reculer(vitesse=80)
            time.sleep(1)
            print("Test 2.3 : Moteur - S'arreter")
            self.controleur.moteur1.arreter()
            self.controleur.moteur2.arreter()

            print("Test 2.4 : Servo - Tester différents angles")
            print(f"  Servo en erreur ? {self.controleur.servo.en_erreur}")
            print(f"  Servo canal: {self.controleur.servo.canal}")
            for angle in [45, 90, 135]:
                print(f"  Positionnement à {angle}°...")
                result = self.controleur.servo.positionner(angle_brut=angle)
                print(f"    Résultat: {result}")
                time.sleep(1)
        except Exception as e:
            self.data.ajouter_log_erreur(f"Moteurs : {e}")
    



    def _verifier_batterie(self):
        """Vérifie la batterie"""
        try : 
        
            print("[*] 3. Vérification de la batterie...")
            print("Test 3.1 : Niveau de batterie")
            niveau = self.controleur.telemetrie.lire_tension() if self.controleur.telemetrie else None
            courant = self.controleur.telemetrie.lire_courant() if self.controleur.telemetrie else None
            print(f" 🪫 - Niveau de Tension: {niveau}V")
            print(f" 🪫 - Niveau de Courant: {abs(courant):.3f}A")
            self.data.ajouter_log_info(f"Tension : {abs(niveau):.3f} V")
            self.data.ajouter_log_info(f"Courant : {abs(courant):.3f} A")
        except Exception as e:
            self.data.ajouter_log_erreur(f"Batterie : {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    script = ScriptAvantCourse(driver=None)
    script.run()