import unittest
from unittest.mock import patch

from src.controllers.GestionSecurite import GestionSecurite


class TestGestionSecurite(unittest.TestCase):
    def setUp(self):
        self.gestion = GestionSecurite(controleur=None)

    @patch("src.controllers.GestionSecurite.time.time", return_value=100.0)
    def test_obstacle_devant_declenche_un_recul(self, _mock_time):
        commande = self.gestion.verifier_securite_distance(8, 28, 12)

        self.assertEqual(commande["action"], "reculer")
        self.assertEqual(commande["angle"], self.gestion.ANGLE_GAUCHE)
        self.assertEqual(commande["raison"], "recul_evitement")

    @patch("src.controllers.GestionSecurite.time.time")
    def test_manoeuvre_enchaine_recul_puis_relance(self, mock_time):
        mock_time.side_effect = [10.0, 10.2, 10.7]

        premiere_commande = self.gestion.verifier_securite_distance(8, 30, 12)
        deuxieme_commande = self.gestion.verifier_securite_distance(30, 30, 12)
        troisieme_commande = self.gestion.verifier_securite_distance(30, 30, 12)

        self.assertEqual(premiere_commande["action"], "reculer")
        self.assertEqual(deuxieme_commande["action"], "reculer")
        self.assertEqual(troisieme_commande["action"], "avancer")
        self.assertEqual(troisieme_commande["angle"], self.gestion.ANGLE_DROITE)
        self.assertEqual(troisieme_commande["raison"], "relance_evitement")

    def test_correction_couloir_tourne_a_gauche_si_le_mur_droit_est_proche(self):
        commande = self.gestion.verifier_securite_distance(60, 10, 24)

        self.assertEqual(commande["action"], "avancer")
        self.assertGreater(commande["angle"], self.gestion.ANGLE_TOUT_DROIT)
        self.assertEqual(commande["vitesse"], self.gestion.VITESSE_RALENTI)

    @patch("src.controllers.GestionSecurite.time.time", return_value=200.0)
    def test_couloir_tres_serre_declenche_un_recul_roues_droites(self, _mock_time):
        commande = self.gestion.verifier_securite_distance(8, 10, 9)

        self.assertEqual(commande["action"], "reculer")
        self.assertEqual(commande["angle"], self.gestion.ANGLE_TOUT_DROIT)

    @patch("src.controllers.GestionSecurite.time.time", return_value=300.0)
    def test_arret_urgence_seulement_apres_plusieurs_blocages(self, _mock_time):
        with patch.object(self.gestion, "arreter_urgence") as mock_arret:
            for _ in range(self.gestion.MAX_BLOCAGES_CONSECUTIFS):
                self.gestion._phase_manoeuvre = None
                commande = self.gestion.verifier_securite_distance(8, 9, 9)
                self.assertIsNotNone(commande)

            self.gestion._phase_manoeuvre = None
            commande_finale = self.gestion.verifier_securite_distance(6, 9, 9)

        self.assertIsNone(commande_finale)
        mock_arret.assert_called_once()


if __name__ == "__main__":
    unittest.main()
