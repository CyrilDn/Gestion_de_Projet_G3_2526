"""
Controleur principal de la voiture.
"""

import os
import sys
import time

import Adafruit_PCA9685
import RPi.GPIO as GPIO

# Ajouter le dossier parent (src) au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.GestionSecurite import GestionSecurite
from materiel.actionneurs.PiloteMoteur_L298N import PiloteMoteur_L298N
from materiel.actionneurs.PiloteServo_PCA9685 import ServoDirectionPCA
from materiel.capteurs.CapteurCouleur import CapteurCouleur
from materiel.capteurs.CapteurUltrason import CapteurUltrason
from materiel.capteurs.DetecteurLigneArrivee_IR import DetecteurLigneArrivee
from materiel.energie.Telemetrie_INA219 import Telemetrie_INA219
from models.SystemData import Data


class ControleurVoiture:
    """Controleur principal de la voiture autonome."""

    def __init__(self):
        """Initialiser tous les composants."""
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

        self.data = Data()
        self._en_marche = False
        self._compteur_tours = 0
        self._dernier_passage_arrivee = 0
        self._arrivee_armee = False
        self.gestion_securite = GestionSecurite(controleur=self)

        self._initialiser_composants()

    def _initialiser_composants(self):
        """Initialiser les capteurs et actionneurs."""
        try:
            print("[*] Initialisation des composants...")
            self.data.ajouter_log_info("Initialisation des composants")

            self._pca = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
            self._pca.set_pwm_freq(50)

            GPIO.setmode(GPIO.BCM)

            self._moteur1 = PiloteMoteur_L298N(
                pin_in1=23,
                pin_in2=18,
                canal_pwm=5,
                pca=self._pca,
            )
            self._moteur2 = PiloteMoteur_L298N(
                pin_in1=27,
                pin_in2=22,
                canal_pwm=4,
                pca=self._pca,
            )

            self._servo = ServoDirectionPCA(canal=0, pca=self._pca)

            self._capteur_ultrason1 = CapteurUltrason(
                pin_trigger=6,
                pin_echo=5,
            )
            self._capteur_ultrason2 = CapteurUltrason(
                pin_trigger=26,
                pin_echo=19,
            )
            self._capteur_ultrason3 = CapteurUltrason(
                pin_trigger=11,
                pin_echo=9,
            )

            self._capteur_couleur = CapteurCouleur(adresse_i2c=0x29)
            self._capteur_couleur.initialiser()
            self._detecteur_arrivee = DetecteurLigneArrivee(pin_capteur=20)
            self._telemetrie = Telemetrie_INA219(adresse_i2c=0x44)

            print("[OK] Composants initialises avec succes")
            self.data.ajouter_log_info("Composants initialises avec succes")
        except Exception as e:
            print(f"[ERREUR] Initialisation impossible: {e}")
            self.data.ajouter_log_erreur(f"Erreur lors de l'initialisation: {e}")
            chemin = self.data.generer_log()
            print(f"[LOG] Logs sauvegardes dans : {chemin}")
            self.gestion_securite.arreter_urgence()
            sys.exit(1)

    # ===== Methodes publiques =====

    def arreter_moteurs(self):
        """Arreter les deux moteurs."""
        if self._moteur1:
            self._moteur1.arreter()
        if self._moteur2:
            self._moteur2.arreter()

    def avancer_moteurs(self, vitesse):
        """Faire avancer les moteurs a une vitesse donnee (0-100)."""
        if self._moteur1:
            self._moteur1.avancer(vitesse=vitesse)
        if self._moteur2:
            self._moteur2.avancer(vitesse=vitesse)

    def reculer_moteurs(self, vitesse):
        """Faire reculer les moteurs a une vitesse donnee (0-100)."""
        if self._moteur1:
            self._moteur1.reculer(vitesse=vitesse)
        if self._moteur2:
            self._moteur2.reculer(vitesse=vitesse)

    def obtenir_etat_marche(self):
        """Retourner si la voiture est actuellement en marche."""
        return self._en_marche

    def definir_etat_marche(self, etat):
        """Definir l'etat de marche de la voiture."""
        self._en_marche = etat

    def obtenir_distance_ultrason(self, position):
        """Obtenir la distance d'un capteur ultrason (avant/droite/gauche)."""
        if position == "avant":
            return (
                self._capteur_ultrason1.mesurer_distance()
                if self._capteur_ultrason1
                else None
            )
        if position == "droite":
            return (
                self._capteur_ultrason2.mesurer_distance()
                if self._capteur_ultrason2
                else None
            )
        if position == "gauche":
            return (
                self._capteur_ultrason3.mesurer_distance()
                if self._capteur_ultrason3
                else None
            )
        return None

    def obtenir_couleur(self):
        """Retourner la couleur dominante detectee par le capteur couleur."""
        rouge, vert, bleu, clair = (
            self._capteur_couleur.lire_valeurs_brutes()
            if self._capteur_couleur
            else (0, 0, 0, 0)
        )
        return (
            self._capteur_couleur.detecter_couleur_dominante(
                rouge,
                vert,
                bleu,
                clair,
            )
            if self._capteur_couleur
            else "inconnu"
        )

    def obtenir_telemetrie(self):
        """Retourner la tension et le courant actuels."""
        tension = self._telemetrie.lire_tension() if self._telemetrie else None
        courant = self._telemetrie.lire_courant() if self._telemetrie else None
        return tension, courant

    def est_sur_ligne_arrivee(self):
        """Verifier si la voiture est sur la ligne d'arrivee."""
        return (
            self._detecteur_arrivee.est_sur_ligne_arrivee()
            if self._detecteur_arrivee
            else False
        )

    def obtenir_servo(self):
        """Retourner le servo pour le controle de la direction."""
        return self._servo

    def lire_capteurs(self):
        """Lire tous les capteurs et retourner un dictionnaire avec les donnees."""
        try:
            distance1 = (
                self._capteur_ultrason1.mesurer_distance()
                if self._capteur_ultrason1
                else None
            )
        except (TimeoutError, ValueError):
            distance1 = 400

        try:
            distance2 = (
                self._capteur_ultrason2.mesurer_distance()
                if self._capteur_ultrason2
                else None
            )
        except (TimeoutError, ValueError):
            distance2 = 400

        try:
            distance3 = (
                self._capteur_ultrason3.mesurer_distance()
                if self._capteur_ultrason3
                else None
            )
        except (TimeoutError, ValueError):
            distance3 = 400

        arrivee_detectee = (
            self._detecteur_arrivee.est_sur_ligne_arrivee()
            if self._detecteur_arrivee
            else False
        )

        tension = self._telemetrie.lire_tension() if self._telemetrie else None
        courant = self._telemetrie.lire_courant() if self._telemetrie else None

        if tension is not None and courant is not None:
            print(f"[TELEMETRIE] Tension: {tension:.2f} V, Courant: {courant:.2f} mA")
            self.data.ajouter_log_info(
                f"Telemetrie - Tension: {tension:.2f} V, Courant: {courant:.2f} mA"
            )
        else:
            print("[TELEMETRIE] Donnees non disponibles")
            self.data.ajouter_log_erreur("Telemetrie indisponible")

        self.data.ajouter_log_info(
            f"Distances - devant: {distance1}, droite: {distance2}, gauche: {distance3}"
        )

        return {
            "distance_avant": distance1,
            "distance_droite": distance2,
            "distance_gauche": distance3,
            "arrivee_detectee": arrivee_detectee,
            "tension": tension,
            "courant": courant,
        }

    def attendre_feu_vert(self):
        """Attendre le feu vert avant de demarrer la course."""
        while True:
            rouge, vert, bleu, clair = (
                self._capteur_couleur.lire_valeurs_brutes()
                if self._capteur_couleur
                else (0, 0, 0, 0)
            )
            couleur_dominante = (
                self._capteur_couleur.detecter_couleur_dominante(
                    rouge,
                    vert,
                    bleu,
                    clair,
                )
                if self._capteur_couleur
                else "inconnu"
            )
            print(f"[COULEUR] R:{rouge} G:{vert} B:{bleu} C:{clair}")
            print(f"[COULEUR] Couleur dominante: {couleur_dominante}")
            self.data.ajouter_log_info(
                f"Capteur couleur - R:{rouge} G:{vert} B:{bleu} C:{clair} dominante:{couleur_dominante}"
            )

            if couleur_dominante == "vert":
                print("[FEU] Vert detecte -> demarrage")
                self.data.ajouter_log_info("Feu vert detecte - demarrage de la course")
                return

            if couleur_dominante == "aucune":
                print("[FEU] Aucune couleur detectee")
                self.gestion_securite.arreter_urgence()
                self.data.ajouter_log_erreur(
                    "Arret d'urgence declenche (feu/capteur couleur)"
                )
                sys.exit(1)

            print(f"[FEU] En attente du vert (capteur: {couleur_dominante})")
            self.arreter_moteurs()
            time.sleep(0.1)

    def _appliquer_commande_conduite(
        self,
        commande,
        tension,
        distance1,
        distance2,
        distance3,
    ):
        """Appliquer la commande moteur/servo calculee par la logique de securite."""
        action = commande.get("action", "arreter")
        vitesse = int(commande.get("vitesse", 0))
        angle = int(commande.get("angle", 90))
        raison = commande.get("raison", "commande")

        if self._servo:
            self._servo.positionner(angle)

        if action == "avancer" and vitesse > 0:
            self.avancer_moteurs(vitesse=vitesse)
            vitesse_signee = vitesse
        elif action == "reculer" and vitesse > 0:
            self.reculer_moteurs(vitesse=vitesse)
            vitesse_signee = -vitesse
        else:
            self.arreter_moteurs()
            vitesse_signee = 0

        niveau_batterie = int(tension) if tension is not None else 0
        self.data.actualise(
            vitesse=vitesse_signee,
            batterie=niveau_batterie,
            angle_roue=angle,
        )
        self.data.actualiser_distances(distance1, distance2, distance3)
        self.data.ajouter_log_info(
            f"Commande {action} - vitesse: {vitesse}% - angle: {angle} - raison: {raison}"
        )

    def _mettre_a_jour_compteur_tours(self, arrivee_detectee, nombre_tour):
        """Compter un tour seulement apres avoir quitte puis recroise la ligne."""
        if not arrivee_detectee:
            self._arrivee_armee = True
            return False

        if not self._arrivee_armee:
            return False

        maintenant = time.time()
        if maintenant - self._dernier_passage_arrivee <= 2:
            return False

        self._dernier_passage_arrivee = maintenant
        self._arrivee_armee = False
        self._compteur_tours += 1
        print(f"Passage ligne arrivee - tour {self._compteur_tours}/{nombre_tour}")
        self.data.ajouter_log_info(f"Tour {self._compteur_tours}/{nombre_tour}")
        self.data.actualiser_nombre_tours(self._compteur_tours, nombre_tour)
        return self._compteur_tours >= nombre_tour

    def run(self, nombre_tour=1, resume=False):
        """Boucle principale de controle."""
        try:
            print("[*] Demarrage de la boucle principale...")
            self.data.ajouter_log_info("Demarrage de la boucle principale")

            if resume:
                import json

                tours_file = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "models",
                    "tours.json",
                )
                if os.path.exists(tours_file):
                    with open(tours_file, "r", encoding="utf-8") as f:
                        tours_data = json.load(f)
                    self._compteur_tours = tours_data.get("nombre_actuel", 0)
                    print(f"[*] Redemarrage - Tours effectues: {self._compteur_tours}")
                    self.data.ajouter_log_info(
                        f"Redemarrage - Tours effectues: {self._compteur_tours}"
                    )
                    self._en_marche = True
                else:
                    print("[!] Fichier tours.json non trouve pour le redemarrage")
                    self.data.ajouter_log_erreur(
                        "Fichier tours.json non trouve pour le redemarrage"
                    )

            self.data.actualiser_nombre_tours(self._compteur_tours, nombre_tour)

            while True:
                capteurs = self.lire_capteurs()
                distance1 = capteurs["distance_avant"]
                distance2 = capteurs["distance_droite"]
                distance3 = capteurs["distance_gauche"]
                arrivee_detectee = capteurs["arrivee_detectee"]
                tension = capteurs["tension"]

                if not self._en_marche:
                    self.attendre_feu_vert()
                    self._en_marche = True

                if self._en_marche:
                    if self._mettre_a_jour_compteur_tours(arrivee_detectee, nombre_tour):
                        print("Fin de course")
                        self.data.ajouter_log_info("Fin de la course !")
                        self.arreter_moteurs()
                        break

                    commande = self.gestion_securite.verifier_securite_distance(
                        distance1,
                        distance2,
                        distance3,
                    )

                    if commande is None:
                        self.data.ajouter_log_erreur(
                            "Arret d'urgence declenche (obstacle critique)"
                        )
                        break

                    self._appliquer_commande_conduite(
                        commande=commande,
                        tension=tension,
                        distance1=distance1,
                        distance2=distance2,
                        distance3=distance3,
                    )

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[*] Arret demande par l'utilisateur")
            self.data.ajouter_log_info("Arret demande par l'utilisateur")
        except Exception as e:
            print(f"[ERREUR] {e}")
            self.data.ajouter_log_erreur(f"Erreur dans la boucle principale: {e}")
        finally:
            self.gestion_securite.arreter_urgence()
            self.data.ajouter_log_info("Arret d'urgence final et fin de session")
            chemin = self.data.generer_log()
            print(f"[LOG] Logs sauvegardes dans : {chemin}")


def main():
    """Point d'entree du programme."""
    nombre_tours = 1
    resume = False

    if len(sys.argv) > 1:
        try:
            nombre_tours = int(sys.argv[1])
        except ValueError:
            nombre_tours = 3

    if "--resume" in sys.argv:
        resume = True

    controleur = ControleurVoiture()
    controleur.run(nombre_tours, resume)


if __name__ == "__main__":
    main()
