import unittest
import os
import datetime
from src.models.SystemData import Data
 
 
class TestActualise(unittest.TestCase):
    """Tests de la méthode actualise()"""
 
    def setUp(self):
        self.data = Data()
 
    def test_actualise_vitesse(self):
        """Vérifie que la vitesse est bien mise à jour"""
        self.data.actualise(12.5, 80, 45)
        self.assertEqual(self.data.vitesse_actuelle, 12.5)
 
    def test_actualise_batterie(self):
        """Vérifie que le niveau de batterie est bien mis à jour"""
        self.data.actualise(12.5, 80, 45)
        self.assertEqual(self.data.niveau_batterie, 80)
 
    def test_actualise_angle_roue(self):
        """Vérifie que l'angle de roue est bien mis à jour"""
        self.data.actualise(12.5, 80, 45)
        self.assertEqual(self.data.angle_roue, 45)
 
 
class TestAjouterLogErreur(unittest.TestCase):
    """Tests de la méthode ajouter_log_erreur()"""
 
    def setUp(self):
        self.data = Data()
 
    def test_erreur_ajoutee_dans_liste(self):
        """Vérifie qu'une erreur est bien ajoutée dans self.logs"""
        self.data.ajouter_log_erreur("Moteur bloqué")
        self.assertEqual(len(self.data.logs), 1)
 
    def test_contenu_erreur(self):
        """Vérifie que le message d'erreur contient [ERROR] et le message"""
        self.data.ajouter_log_erreur("Moteur bloqué")
        self.assertIn("[ERROR]", self.data.logs[0])
        self.assertIn("Moteur bloqué", self.data.logs[0])
 
    def test_horodatage_present(self):
        """Vérifie que l'horodatage est présent dans l'entrée"""
        self.data.ajouter_log_erreur("Tension trop élevée")
        date_aujourdhui = datetime.datetime.now().strftime("%Y-%m-%d")
        self.assertIn(date_aujourdhui, self.data.logs[0])
 
    def test_plusieurs_erreurs(self):
        """Vérifie que plusieurs erreurs s'accumulent bien dans la liste"""
        self.data.ajouter_log_erreur("Erreur 1")
        self.data.ajouter_log_erreur("Erreur 2")
        self.data.ajouter_log_erreur("Erreur 3")
        self.assertEqual(len(self.data.logs), 3)
 
    def test_liste_vide_au_depart(self):
        """Vérifie que la liste est vide à l'initialisation"""
        self.assertEqual(self.data.logs, [])
 
 
class TestGenererLog(unittest.TestCase):
    """Tests de la méthode generer_log()"""
 
    def setUp(self):
        self.data = Data()
 
    def test_fichier_cree(self):
        """Vérifie que le fichier .log est bien créé sur disque"""
        chemin = self.data.generer_log()
        self.assertTrue(os.path.exists(chemin))
 
    def test_nom_fichier_correct(self):
        """Vérifie que le nom du fichier commence par 'voiture_'"""
        chemin = self.data.generer_log()
        nom = os.path.basename(chemin)
        self.assertTrue(nom.startswith("voiture_"))
        self.assertTrue(nom.endswith(".log"))
 
    def test_fichier_contient_rapport(self):
        """Vérifie que le fichier contient l'en-tête du rapport"""
        chemin = self.data.generer_log()
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
        self.assertIn("RAPPORT DE COURSE", contenu)
 
    def test_fichier_contient_erreurs(self):
        """Vérifie que les erreurs ajoutées apparaissent dans le fichier"""
        self.data.ajouter_log_erreur("Capteur ultrason KO")
        chemin = self.data.generer_log()
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
        self.assertIn("Capteur ultrason KO", contenu)
 
    def test_fichier_aucune_erreur(self):
        """Vérifie le message quand aucune erreur n'a été enregistrée"""
        chemin = self.data.generer_log()
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
        self.assertIn("Aucune erreur enregistrée durant cette course.", contenu)
 
    def test_liste_videe_apres_generation(self):
        """Vérifie que self.logs est réinitialisé après generer_log()"""
        self.data.ajouter_log_erreur("Erreur test")
        self.data.generer_log()
        self.assertEqual(self.data.logs, [])
 
    def test_nombre_tour_dans_fichier(self):
        """Vérifie que le nombre de tours apparaît dans le fichier"""
        self.data.nombre_tour = 3
        chemin = self.data.generer_log()
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
        self.assertIn("3", contenu)
 
 
if __name__ == "__main__":
    unittest.main()