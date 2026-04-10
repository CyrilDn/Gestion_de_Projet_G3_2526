import os
import sys

# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time


class CompteurLigne:
    def __init__(self, driver):
        self.driver = driver
        self.controleur = ControleurVoiture()
        self.data = Data()

    def run(self):
        try:
            print("\n" + "=" * 40)
            print("TESTS DU COMPTEUR DE PASSE DE LA LIGNE D'ARRIVEE")
            print("=" * 40)
            time.sleep(1)

            self._verifier_compteur(nombre_tours=3)

            self.controleur.moteur1.arreter()
            self.controleur.moteur2.arreter()

            print("\n" + "=" * 40)
            print(" ✅ FIN")
            print("=" * 40 + "\n")

        except Exception as e:
            self.data.ajouter_log_erreur(f"Erreur critique : {e}")
            print(f" ❌ Erreur: {e}")

        chemin = self.data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")

    def _verifier_compteur(self, nombre_tours):
        """Verfifie les compteur de ligne d'arrivee pour faire plusieurs tours"""

        try:
            self.controleur.moteur1.avancer(vitesse=50)
            self.controleur.moteur2.avancer(vitesse=50)

            print("Lancement de la boucle")
            count = 0
            while count < nombre_tours + 1:
                try:
                    valeur = (
                        self.controleur.detecteur_arrivee.est_pas_sur_ligne_arrivee()
                    )
                    self.data.ajouter_log_info(f"Ligne d'arrivée : {valeur}")
                    print(
                        f"  - Valeur détectée: {valeur} | Nombre de tours restant : {nombre_tours - count}"
                    )
                    if valeur:
                        count += 1
                        time.sleep(3)

                except Exception as e:
                    print(f"  - ERREUR Capteur Ligne: {e}")
                    self.data.ajouter_log_erreur(f"Capteur Ligne: {e}")

        except Exception as e:
            self.data.ajouter_log_erreur(f"Erreur capteurs: {e}")
            print(f"[✗] Erreur générale capteurs: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    script = CompteurLigne(driver=None)
    script.run()
