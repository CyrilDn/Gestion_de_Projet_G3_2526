# Projet Voiture - Gestion G3 2025/2026

## 📋 Description
Projet de gestion et contrôle d'un véhicule autonome avec système de capteurs et d'actionneurs.

## 🏗️ Architecture du Projet

### Structure
```
src/
├── controllers/     # Logique de contrôle
├── materiel/       # Interfaces matériel
│   ├── actionneurs/   # Moteurs, servos
│   ├── capteurs/      # Détecteurs, capteurs
│   └── energie/       # Gestion de l'énergie
├── models/         # Modèles de données
└── views/          # Interfaces de visualisation

tests/              # Suite de tests
```

## 🔧 Composants Principaux

### Actionneurs
- **PiloteMoteur_L298N**: Contrôle moteur DC L298N
- **PiloteServo_PCA9685**: Contrôle servomoteurs via PCA9685

### Capteurs
- **CapteurCouleur**: Détection de couleur
- **CapteurUltrason**: Mesure de distance (HC-SR04)
- **DetecteurLigneArrivee_IR**: Détecteur infrarouge ligne d'arrivée

### Énergie
- **Telemetrie_INA219**: Monitoring consommation énergétique

## ✅ Tests
```bash
# Lancer les tests
python3 -m unittest tests/le test a tester
```