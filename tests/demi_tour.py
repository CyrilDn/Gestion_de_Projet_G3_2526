import os
import sys
# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time

class ScriptDemiTour:
    def __init__(self):
        self._controleur = ControleurVoiture()
        self._data = Data()

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

        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
            raise
        except Exception as e:
            print(f"[✗] Erreur: {e}")
        finally:
            self._controleur.gestion_securite.arreter_urgence()
        
        chemin = self._data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")

    def _effectuer_demi_tour(self):
        """Effectue un demi-tour"""
        try:
            print("[*] 1. Effectuer un demi-tour...")
            self._controleur._servo.positionner(angle_brut = 90)  # On s'assure que les roues sont droites
            """Manœuvre 1"""
            self._controleur._servo.positionner(angle_brut = 45)  # Tourne à gauche de 45 degrés
            time.sleep(0.5)  
            self._controleur._moteur1.avancer(vitesse = 40)  # Avance légèrement pour compléter le demi-tour
            self._controleur._moteur2.avancer(vitesse = 40)
            time.sleep(1)  
            self._controleur._moteur1.arreter()  # Arrête les moteurs
            self._controleur._moteur2.arreter()
            time.sleep(0.5)
            #self._controleur._servo.positionner(angle_brut = 90)  # Recentrer le servo
            #time.sleep(0.5)
            self._controleur._servo.positionner(angle_brut = 135)  # Tourne à droite de 135 degrés
            time.sleep(0.5)

            """Manœuvre 2"""
            self._controleur._moteur1.reculer(vitesse = 40)  # Recule légèrement pour compléter le demi-tour
            self._controleur._moteur2.reculer(vitesse = 40) 
            time.sleep(1)
            self._controleur._moteur1.arreter()  # Arrête les moteurs
            self._controleur._moteur2.arreter()
            time.sleep(0.5)
            #self._controleur._servo.positionner(angle_brut = 90)  # Recentrer le servo
            #time.sleep(0.5)

            """Manœuvre 3"""
            self._controleur._servo.positionner(angle_brut = 45)  # Tourne à gauche de 45 degrés
            time.sleep(0.5)
            self._controleur._moteur1.avancer(vitesse = 40)  # Avance légèrement pour compléter le demi-tour
            self._controleur._moteur2.avancer(vitesse = 40)
            time.sleep(1)
            self._controleur._moteur1.arreter()  # Arrête les moteurs
            self._controleur._moteur2.arreter()
            time.sleep(0.5)
            self._controleur._servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(0.5)


        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
            raise
        except Exception as e:
            print(f"[✗] Erreur: {e}")
        finally:
            self._controleur.gestion_securite.arreter_urgence()

        self._data.ajouter_log_info("Demi-tour effectué avec succès.")



def main():
    """Point d'entrée du programme"""
    demi = ScriptDemiTour()
    demi.run()


if __name__ == "__main__":
    main()