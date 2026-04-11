import os
import sys

# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time


class Tour8:
    def __init__(self, driver):
        self._driver = driver
        self._controleur = ControleurVoiture()
        self._data = Data()
    def run(self):
        try:
            print("\n" + "=" * 40)
            print(" 🚀 DÉMARRAGE DU TOUR EN 8")
            print("=" * 40)
            time.sleep(1)

            self._lancer_tour8(1)

            self._controleur._moteur1.arreter()
            self._controleur._moteur2.arreter()

            time.sleep(1)

            print("\n" + "=" * 40)
            print(" ✅ LA VOITURE A FINI SON TOUR")
            print("=" * 40 + "\n")

        except Exception as e:
            self._data.ajouter_log_erreur(f"Erreur critique : {e}")
            print(f" ❌ Erreur: {e}")

        chemin = self._data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")

    def _lancer_tour8(self, nb_huit=3):
        print("Lancement du Tour en 8 ...")

        # On lance les moteurs
        self._controleur._moteur1.avancer(vitesse=50)
        self._controleur._moteur2.avancer(vitesse=50)

        for _ in range(nb_huit):
            # boucle gauche
            self._controleur._servo.positionner(angle_brut=45)
            time.sleep(4)  # durée pour boucler complètement à gauche

            # centre
            self._controleur._servo.positionner(angle_brut=90)
            # time.sleep(0.5)  # bref moment en ligne droite pour croiser

            # boucle droite
            self._controleur._servo.positionner(angle_brut=135)
            time.sleep(3.4)  # durée pour boucler complètement à droite

            # retour centre
            self._controleur._servo.positionner(angle_brut=90)
            # time.sleep(0.5)


if __name__ == "__main__":
    script = Tour8(driver=None)
    script.run()
