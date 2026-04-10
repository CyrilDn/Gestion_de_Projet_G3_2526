import os
import sys
# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time

class ScriptDemiTour:
    def __init__(self):
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

        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
            raise
        except Exception as e:
            print(f"[✗] Erreur: {e}")
        finally:
            self.controleur.arreter_urgence()
        
        chemin = self.data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")

    def _effectuer_demi_tour(self):
        """Effectue un demi-tour"""
        try:
            print("[*] 1. Effectuer un demi-tour...")
            self.controleur.servo.positionner(angle_brut = 90)  # On s'assure que les roues sont droites

            """Manœuvre 1"""
            self.controleur.servo.positionner(angle_brut = 45)  # Tourne à gauche de 45 degrés
            time.sleep(2)  
            self.controleur.moteur1.avancer(vitesse = 40)  # Avance légèrement pour compléter le demi-tour
            self.controleur.moteur2.avancer(vitesse = 40)
            time.sleep(2)  
            self.controleur.moteur1.arreter()  # Arrête les moteurs
            self.controleur.moteur2.arreter()
            time.sleep(1)
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(1)
            self.controleur.servo.positionner(angle_brut = 135)  # Tourne à droite de 135 degrés
            time.sleep(2)
            self.controleur.moteur1.reculer(vitesse = 40)  # Recule légèrement pour compléter le demi-tour
            self.controleur.moteur2.reculer(vitesse = 40) 
            time.sleep(2)
            self.controleur.moteur1.arreter()  # Arrête les moteurs
            self.controleur.moteur2.arreter()
            time.sleep(1)
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(1)

            """Manoeuvre 2"""
            self.controleur.servo.positionner(angle_brut = 45)  # Tourne à gauche de 45 degrés
            time.sleep(2)  
            self.controleur.moteur1.avancer(vitesse = 40)  # Avance légèrement pour compléter le demi-tour
            self.controleur.moteur2.avancer(vitesse = 40)
            time.sleep(2)  
            self.controleur.moteur1.arreter()  # Arrête les moteurs
            self.controleur.moteur2.arreter()
            time.sleep(1)
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(1)
            self.controleur.servo.positionner(angle_brut = 135)  # Tourne à droite de 135 degrés
            time.sleep(2)
            self.controleur.moteur1.reculer(vitesse = 40)  # Recule légèrement pour compléter le demi-tour
            self.controleur.moteur2.reculer(vitesse = 40)
            time.sleep(2)
            self.controleur.moteur1.arreter()  # Arrête les moteurs
            self.controleur.moteur2.arreter()
            time.sleep(1)
            self.controleur.servo.positionner(angle_brut = 90)  # Recentrer le servo
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[*] Arrêt demandé par l'utilisateur")
            raise
        except Exception as e:
            print(f"[✗] Erreur: {e}")
        finally:
            self.controleur.arreter_urgence()

        self.data.ajouter_log_info("Demi-tour effectué avec succès.")




def main():
    """Point d'entrée du programme"""
    demi = ScriptDemiTour()
    demi.run()


if __name__ == "__main__":
    main()