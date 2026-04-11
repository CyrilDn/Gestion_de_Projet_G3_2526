import os
import sys

# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.ControleurVoiture import ControleurVoiture
from src.models.SystemData import Data

import time


class ResetServo:
    def __init__(self, driver):
        self._driver = driver
        self._controleur = ControleurVoiture()
        self._data = Data()

    def run(self):
        try:
            print("\n" + "=" * 40)
            print(" 🚀 DÉMARRAGE DU RESET")
            print("=" * 40)
            time.sleep(1)

            self._lancer_reset()
            time.sleep(1)

            print("\n" + "=" * 40)
            print(" ✅ LA VOITURE A FINI SON TOUR")
            print("=" * 40 + "\n")

        except Exception as e:
            self._data.ajouter_log_erreur(f"Erreur critique : {e}")
            print(f" ❌ Erreur: {e}")

        chemin = self._data.generer_log()
        print(f"\n📄 Logs sauvegardés dans : {chemin}")

    def _lancer_reset(self):
        print("Reset ...")
        self._controleur._servo.positionner(angle_brut=90)
        time.sleep(1)


if __name__ == "__main__":
    script = ResetServo(driver=None)
    script.run()
