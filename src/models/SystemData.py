import os
import datetime

class Data():
    """
    Modèle central de données de la voiture.
    Stocke les valeurs des capteurs en temps réel et gère les logs d'erreurs.
    """

    LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")

    def __init__(self):
        self.vitesse_actuelle: float = 0.0
        self.niveau_batterie: int = 0
        self.angle_roue: int = 0
        self.nombre_tour: int = 0
        self.logs: list = [] 


    def actualise(self, vitesse:float, batterie:int,angle_roue): 
        self.vitesse_actuelle = vitesse
        self.niveau_batterie = batterie
        self.angle_roue = angle_roue


    def ajouter_log_erreur(self, erreur):
        horodatage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entree = f"[ERROR] [{horodatage}] {erreur}"
        self.logs.append(entree)
        print(entree)


    def ajouter_log_info(self, message):
        horodatage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entree = f"[INFO]  [{horodatage}] {message}"
        self.logs.append(entree)
        print(entree)
        

    def generer_log(self):

        os.makedirs(self.LOGS_DIR, exist_ok=True)
 
        # Nom du fichier : voiture_YYYYMMDD_HHMMSS.log
        horodatage_fichier = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"voiture_{horodatage_fichier}.log"
        chemin_fichier = os.path.join(self.LOGS_DIR, nom_fichier)

        with open(chemin_fichier, "w", encoding="utf-8") as fichier_log:
            fichier_log.write(f"=== RAPPORT DE COURSE — {horodatage_fichier} ===\n")
            fichier_log.write(f"Nombre de tours effectués : {self.nombre_tour}\n")
            fichier_log.write(f"{'=' * 50}\n\n")

            if self.logs:
                for entree in self.logs:
                    fichier_log.write(entree + "\n")
            else:
                fichier_log.write("Aucune erreur enregistrée durant cette course.\n")

            fichier_log.write(f"\n{'=' * 50}\n")
            fichier_log.write("=== FIN DU RAPPORT ===\n")

        self.logs = []  # liste vide pour prochaine course
        return chemin_fichier


