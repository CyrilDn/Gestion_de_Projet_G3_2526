import unittest
import logging

from unittest.mock import MagicMock

from src.materiel.energie.Telemetrie_INA219 import Telemetrie_INA219


class TestTelemetrieINA219(unittest.TestCase):
    def setUp(self):
        # Création d'un faux bus I2C
        self.mock_bus_i2c = MagicMock()
        self.adresse = "0x40"
        self.telemetrie = Telemetrie_INA219(self.adresse, self.mock_bus_i2c)

    def test_lire_tension_nominale(self):
        """Vérifie que la lecture de la tension fonctionne correctement."""
        self.mock_bus_i2c.read_voltage.return_value = 5.2  # 5.2 Volts

        tension = self.telemetrie.lire_tension()

        self.assertEqual(tension, 5.2)
        self.mock_bus_i2c.read_voltage.assert_called_once_with(self.adresse)

    def test_erreur_lecture_retourne_valeur_securite(self):
        """Cas limite : Timeout ou déconnexion I2C. Doit retourner float('inf')."""
        # On simule une exception levée par la librairie I2C (ex: IOError)
        self.mock_bus_i2c.read_current.side_effect = IOError("Bus I2C injoignable")

        courant = self.telemetrie.lire_courant()

        # Vérifie que la valeur par défaut est l'infini pour déclencher les sécurités
        self.assertEqual(courant, float("inf"))
        self.mock_bus_i2c.read_current.assert_called_once_with(self.adresse)

    def test_verifier_surcharge_declenchement_normal(self):
        """Cas limite : Le moteur bloque, le courant dépasse la limite."""
        limite = 0.75  # Limite à 0.75 Ampères
        self.mock_bus_i2c.read_current.return_value = 1  # Surcharge mécanique

        est_en_surcharge = self.telemetrie.verifier_surcharge(limite)

        self.assertTrue(est_en_surcharge)

    def test_verifier_surcharge_hysteresis(self):
        """Cas limite : Stabilité des mesures. Vérifie le comportement de l'hystérésis."""
        limite = 0.75
        marge = self.telemetrie.marge_hysteresis

        # 1. Le courant dépasse la limite : SURCHARGE
        self.mock_bus_i2c.read_current.return_value = 0.8
        self.assertTrue(self.telemetrie.verifier_surcharge(limite))

        # 2. Le courant redescend JUSTE en dessous de la limite (ex: 0.7 A).
        # L'hystérésis doit maintenir l'état de surcharge pour éviter les rebonds.
        self.mock_bus_i2c.read_current.return_value = limite - (marge / 2)
        self.assertTrue(self.telemetrie.verifier_surcharge(limite))

        # 3. Le courant descend sous le seuil d'hystérésis (retour à la normale).
        self.mock_bus_i2c.read_current.return_value = limite - marge - 0.05
        self.assertFalse(self.telemetrie.verifier_surcharge(limite))

    def test_surcharge_forcee_en_cas_derreur_capteur(self):
        """Garde-fou : Si le capteur est débranché en roulant, on coupe tout."""
        self.mock_bus_i2c.read_current.side_effect = TimeoutError("Mesure trop longue")

        # verifier_surcharge doit lire float('inf') via lire_courant() et passer à True
        est_en_surcharge = self.telemetrie.verifier_surcharge(limite_courant=0.75)

        self.assertTrue(est_en_surcharge)


if __name__ == "__main__":
    # Désactive les logs d'erreur pendant les tests pour garder la console propre
    logging.disable(logging.CRITICAL)
    unittest.main()
