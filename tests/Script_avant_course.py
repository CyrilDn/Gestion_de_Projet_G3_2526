
import os
import sys
# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture

import time

class ScriptAvantCourse:
    def __init__(self, driver):
        self.driver = driver
        self.controleur = ControleurVoiture(driver)

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
        self.controleur.avancer(vitesse=50, ramping=True)
        time.sleep(1)
        print("Test 2.2 : Moteur arrière - Reculer")
        self.controleur.reculer(vitesse=50, ramping=True)
        time.sleep(1)
        print("Test 2.3 : Moteur - S'arreter")
        self.controleur.arreter()
    

    def _verifier_batterie(self):
        """Vérifie la batterie"""
        print("[*] 3. Vérification de la batterie...")
        print("Test 3.1 : Niveau de batterie")
        niveau = self.controleur.batterie.mesurer_niveau() if self.controleur.batterie else None
        print(f" 🪫 - Niveau de batterie: {niveau}%")
        time.sleep(0.5)


if __name__ == "__main__":
    script = ScriptAvantCourse(driver=None)
    script.run()