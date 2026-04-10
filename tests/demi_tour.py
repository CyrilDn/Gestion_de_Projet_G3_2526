import os
import sys
# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time

class ScriptDemiTour:
    def __init__(self, driver):
        self.driver = driver
        self.controleur = ControleurVoiture()
        self.data = Data()

    def run(self):
        try:
            print("\n" + "="*40)
            print(" 🔄 DÉMARRAGE DU CHECK-UP - Script Demi-Tour")
            print("="*40)
            time.sleep(1)

            self._effectuer_demi_tour()

            print("\n" + "="*40)
            print(" ✅ DEMI-TOUR RÉUSSI !")
            print(" ✅ LA VOITURE EST PRÊTE POUR LA COURSE.")
            print("="*40 + "\n")

        except Exception as e:
            self.data.ajouter_log_erreur(f"Erreur critique : {e}")
            print(f" ❌ Erreur: {e}")
        
        chemin = self.data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")

    def _effectuer_demi_tour(self):
        """Effectue un demi-tour"""
        try:
            print("[*] 1. Effectuer un demi-tour...")
            # Série 1
            self.controleur.servo.positionner(angle_brut = 45)  # Tourne à gauche de 45 degrés
            time.sleep(1.5)  
            self.controleur.moteur.avancer(vitesse = 50)  # Avance légèrement pour compléter le demi-tour
            time.sleep(1.5)  
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(0.5)
            self.controleur.servo.positionner(angle_brut = 135)  # Tourne à droite de 135 degrés
            time.sleep(1.5)
            self.controleur.moteur.reculer(vitesse = 50)  # Recule légèrement pour compléter le demi-tour
            time.sleep(1.5)
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(0.5)

            #Série 2
            self.controleur.servo.positionner(angle_brut = 45)  # Tourne à gauche de 45 degrés
            time.sleep(1.5)  
            self.controleur.moteur.avancer(vitesse = 50)  # Avance légèrement pour compléter le demi-tour
            time.sleep(1.5)  
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(0.5)
            self.controleur.servo.positionner(angle_brut = 135)  # Tourne à droite de 135 degrés
            time.sleep(1.5)
            self.controleur.moteur.reculer(vitesse = 50)  # Recule légèrement pour compléter le demi-tour
            time.sleep(1.5)
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(0.5)

            self.data.ajouter_log_info("Demi-tour effectué avec succès.")
        except Exception as e:
            self.data.ajouter_log_erreur(f"Erreur lors du demi-tour : {e}")
            raise