import os
import datetime

class Data():
    """
    Modèle central de données de la voiture.
    Stocke les valeurs des capteurs en temps réel et gère les logs d'erreurs.
    """

    def __init__(self):
        self.vitesse_actuelle: float = 0.0
        self.niveau_batterie: int = 0
        self.angle_roue: int = 0
        self.nombre_tour: int = 0
        self.logs: list = [] 


    def actualise():
        pass

    def ajouter_log_erreur():
        pass

    def generer_log():
        pass 