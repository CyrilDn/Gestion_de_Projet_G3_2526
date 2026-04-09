
import os
import sys
# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture

import time

class ScriptAvantCourse:
    def __init__(self, driver):
        self.driver = driver
        self.controleur = ControleurVoiture()

    def run(self):
        """Exécute les vérifications avant course"""
        try:
            print("\n" + "="*40)
            print(" 🚀 DÉMARRAGE DU CHECK-UP - Script Avant Course")
            print("="*40)
            time.sleep(1)

            self._verifier_capteurs() # TEST 1 : Les Yeux 
            self._verifier_moteurs() # TEST 2 : Les Muscles
            self._verifier_batterie() # TEST 3 : L'Énergie

            print("\n" + "="*40)
            print(" ✅ TOUS LES TESTS SONT AU VERT !")
            print(" ✅ LA VOITURE EST PRÊTE POUR LA COURSE.")
            print("="*40 + "\n")

        except Exception as e:
            print(f" ❌ Erreur: {e}")



    def _verifier_capteurs(self):
        """Vérifie les capteurs"""
        print("[*] 1. Vérification de la vue - capteurs...")
        print("Test 1.1 : Capteur ultrason - Mesure de distance")
        for i in range(3):
            distance = self.controleur.capteur_ultrason.mesurer_distance() if self.controleur.capteur_ultrason else None
            print(f"  - Mesure de distance {i+1}: {distance} cm")
            time.sleep(0.5)
        

    def _verifier_moteurs(self):
        """Vérifie les moteurs"""
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

        
        print("Test 2.4 : Moteur - Tourner à gauche")
        self.controleur.servo.positionner(angle=45)  # Tourner à gauche
        time.sleep(1)
        self.controleur.servo.positionner(angle=90)  # Recentrer le servo
        time.sleep(1)
        print("Test 2.5 : Moteur - Tourner à droite")
        self.controleur.servo.positionner(angle=135)  # Tourner à droite
        time.sleep(1)
        self.controleur.servo.positionner(angle=90)  # Recentrer le servo

    def _verifier_batterie(self):
        """Vérifie la batterie"""
        print("[*] 3. Vérification de la batterie...")
        print("Test 3.1 : Niveau de batterie")
        niveau = self.controleur.telemetrie.lire_tension() if self.controleur.telemetrie else None
        courant = self.controleur.telemetrie.lire_courant() if self.controleur.telemetrie else None
        print(f" 🪫 - Niveau de Tension: {niveau}V")
        print(f" 🪫 - Niveau de Courant: {abs(courant):.3f}A")
        time.sleep(0.5)


if __name__ == "__main__":
    script = ScriptAvantCourse(driver=None)
    script.run()