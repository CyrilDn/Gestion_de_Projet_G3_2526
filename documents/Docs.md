# Documentation Technique - Projet Voiture Groupe 3

---

## 🎯 Les Défis Techniques (La Course)

Une fois la base saine, il faudra s'attaquer au comportement routier :

- **Maniabilité (US 7 & 8) :** Faire un « 8 » et un demi-tour dans un espace restreint
- **Évitement (US 9) :** Contourner les obstacles en moins de **15 secondes**
- **Arrêt de précision (US 10) :** S'arrêter à moins de **5 cm** de la ligne d'arrivée via le capteur infrarouge
- **Réactivité (US 13) :** Démarrage automatique dès la détection du signal

---

# 1. Architecture Matérielle de la Voiture

Afin de séparer logiquement les différentes responsabilités du véhicule, les composants matériels ont été classés en trois catégories distinctes : l'acquisition des données (La Vue), la propulsion et la direction (Les Muscles), ainsi que la gestion de l'énergie et du traitement (L'Alimentation & Le Système).

---

## 👁️ La Vue (Acquisition et analyse de l'environnement)

Cette section regroupe les éléments chargés de scruter la piste et de remonter des données brutes vers le système central.

- **Modules Ultrasons HC-SR04 (x3)** : Disposés à l'avant, à l'arrière ou sur les flancs, ces télémètres acoustiques évaluent les distances pour anticiper les collisions et permettre au robot de contourner les obstacles
- **Détecteur IR (Suiveur de ligne)** : Composant optique dont l'unique mission est de distinguer les contrastes forts (ligne sombre sur sol clair) pour garantir le maintien strict de la trajectoire
- **Capteur Colorimétrique TCS3472** : Caméra spécialisée communiquant via I2C. Elle décompose la lumière selon les canaux RGB et Clear pour identifier les signaux sur le circuit

---

## 💪 Les Muscles (Génération du mouvement et actionneurs)

Cette catégorie rassemble les interfaces de puissance et les moteurs qui traduisent les décisions logicielles en déplacements physiques.

- **Moteurs à Courant Continu (x2)** : Blocs de motorisation principaux chargés de la propulsion (accélération, freinage, marche arrière)
- **Servomoteurs (x3)** : Actionneurs de haute précision capables de se positionner sur des angles précis pour orienter les roues ou articuler des mécanismes annexes
- **Pont en H L298N (Driver DC)** : Interface de puissance qui reçoit les ordres de la carte mère et les convertit en courants suffisamment forts pour faire tourner les moteurs, gérant l'inversion de polarité
- **Contrôleur PCA9685 (Driver PWM)** : Module I2C conçu pour générer des signaux PWM stables, déchargeant le processeur de cette tâche répétitive pour un contrôle fluide

---

## ⚡ L'Alimentation & Le Système (Énergie, Télémétrie et Traitement)

Cette section représente le cœur névralgique de la voiture : elle assure la survie électrique du robot et traite les informations.

- **Carte Mère Raspberry Pi 3 B** : Centre décisionnel embarqué qui pilote tous les modules via GPIO et le bus I2C. Intègre Wi-Fi et Bluetooth pour la télémétrie
- **Onduleur PiJuice (HAT)** : Module d'alimentation sans coupure intelligent embarquant la batterie principale et protégeant le Raspberry Pi des baisses de tension
- **Sonde Télémétrique INA219** : Outil de diagnostic branché sur I2C qui surveille la consommation de courant et la tension pour détecter les anomalies
- **Convertisseur XL1509** : Régulateur "abaisseur" (step-down) qui ajuste les tensions de la batterie vers des valeurs exploitables (5V, 3.3V) avec excellent rendement thermique

---

# 2. ⚠️ Exigences et Cas Limites par Catégorie Matérielle

## 💪 1. Les Muscles (Actionneurs & Mouvements)
*Cette catégorie regroupe tout ce qui génère un mouvement physique. Les tests doivent garantir que le système ne casse pas la mécanique.*

### Moteur DC (Propulsion)
**Cas limites à gérer :**
- Ne pas activer le moteur si le signal PWM est inférieur au seuil minimal.
- Identifier le moteur comme probablement bloqué si la vitesse est nulle alors que le PWM est > 50%.

**Tests à implémenter :**
- Gestion du démarrage progressif (ramping) pour éviter les à-coups.
- Inversion de polarité avec l'application d'un délai de sécurité.
- Mesure continue de la vitesse et vérification de sa cohérence avec le signal PWM.

### Servomoteur (Direction)
**Cas limites à gérer :**
- Rejeter ou corriger (restreindre à la plage) toute valeur d'angle < 0 ou > 180.
- Déclencher une réaction de sécurité si le signal PWM est absent ou instable.
- Gérer la présence d'un obstacle physique empêchant d’atteindre l’angle demandé.
- Vérifier la stabilité du moteur si une commande identique est répétée.

**Tests à implémenter :**
- Arrondi ou "cast" propre des valeurs d’angle avant l'envoi au contrôleur.

---

## 👁️ La Vue (Capteurs & Acquisition)

Cette catégorie représente les « yeux » de la Voiture. Les tests doivent filtrer le bruit du monde réel pour ne garder que la donnée fiable.

### Capteur Ultrason (HC-SR04)

**Cas limites à gérer :**
- Considérer la distance comme trop faible si la durée de retour est < 100µs
- Déduire qu'aucun objet n'est détecté si la durée dépasse le timeout (ex : 30ms)
- Identifier comme bruit ou écho multiple les variations brutales entre 2 mesures

**Tests à implémenter :**
- Moyennage de plusieurs mesures successives
- Détection des valeurs aberrantes via seuils ou histogramme
- Calibration des mesures selon la température

### Suiveur de Ligne (Capteur IR)

**Cas limites à gérer :**
- Déclarer la ligne comme perdue si aucun capteur n'est sur la ligne (tous lisent du blanc)
- Donner l'ordre de continuer tout droit si seul le capteur central est sur le noir
- Filtrer les rebonds en cas de lecture trop instable ou de bruit

**Tests à implémenter :**
- Bufferisation des mesures (ex : conserver les 5 dernières valeurs)
- Détection de virage en cas de changement brutal de direction
- Arrêt ou réduction de la vitesse si la ligne n'est pas retrouvée rapidement

### Capteur de Couleur RGB (TCS3472)

**Cas limites à gérer :**
- Traiter la mesure comme saturée si les valeurs du canal clair sont > seuil max
- Déduire que l'objet est trop éloigné ou non détecté si les valeurs RGB = 0
- Considérer que le bruit est dominant si les valeurs lues sont trop faibles

**Tests à implémenter :**
- Normalisation des valeurs RGB sur la base du canal clair
- Détection d'une lumière ambiante trop intense ou trop faible
- Implémentation d'une correction gamma

---

## ⚡ L'Alimentation (Énergie, Télémétrie & Sécurité globale)

Cette catégorie protège l'intégrité électrique du robot et assure la stabilité du système.

### Télémétrie et Surges (Courant / Tension)

**Cas limites à gérer :**
- Désactiver les moteurs par sécurité en cas de tension d'alimentation trop élevée
- Détecter un possible blocage ou surcharge mécanique si le courant mesuré est trop élevé
- Détection d'une surcharge mécanique ou d'un retour en force sur les servomoteurs via le capteur de courant

### Stabilité et Règles Globales

**Tests et garde-fous à implémenter :**
- Vérifier systématiquement la cohérence temporelle des mesures
- Utiliser des seuils de confiance et une hystérésis pour gérer les changements d'état de manière fluide
- Appliquer un timeout systématique sur toute mesure active
- Logger ou retourner une valeur par défaut de sécurité pour tout cas non conforme

---

---

# 3. Arborescence MVC (Suivi des exigences du PWP + interface web pour l'affichage)

```
projet_voiture/
│
├── src/
│   ├── main.py                          # 🚀 Point d'entrée (assemble Modèle, Vue, Contrôleur, Matériel)
│   │
│   ├── models/                          # 📊 LE MODÈLE (Sans dépendance matérielle)
│   │   ├── __init__.py
│   │   └── SystemData.py                # Stocke les valeurs des capteurs
│   │
│   ├── views/                           # 🖥️ LA VUE (Sans dépendance matérielle)
│   │   ├── __init__.py
│   │   ├── web_server.py                # Serveur Flask/FastAPI
│   │   ├── templates/
│   │   │   └── dashboard.html           # Affiche les données du SystemData
│   │   └── static/
│   │       └── style.css
│   │
│   ├── controllers/                     # 🧠 LE CONTRÔLEUR (Sans dépendance matérielle)
│   │   ├── __init__.py
│   │   ├── ControleurVoiture.py         # Cerveau principal (logique de conduite)
│   │   └── GestionSecurite.py           # Logique d'arrêt d'urgence
│   │
│   └── materiel/                        # ⚙️ COUCHE MATÉRIELLE (Mockable pour les tests)
│       ├── __init__.py
│       │
│       ├── actionneurs/                 # 🦾 Les Muscles (Génèrent du mouvement)
│       │   ├── __init__.py
│       │   ├── PiloteMoteur_L298N.py    # Gère les 2 moteurs DC via L298N
│       │   └── PiloteServo_PCA9685.py   # Gère les 3 servomoteurs via PCA9685 I2C
│       │
│       ├── capteurs/                    # 👁️ Les Sens (Lisent l'environnement)
│       │   ├── __init__.py
│       │   ├── Ultrason_HCSR04.py       # Interroge les 3 capteurs ultrason
│       │   ├── SuiveurLigne_IR.py       # Lit le capteur infrarouge de ligne
│       │   └── CapteurCouleur_TCS3472.py # Lit les valeurs RGB via I2C
│       │
│       └── energie/                     # ⚡ L'Alimentation (Surveillance électrique)
│           ├── __init__.py
│           ├── Telemetrie_INA219.py     # Mesure tension/courant via I2C
│           └── Onduleur_PiJuice.py      # Gère le HAT batterie
│           # Note : Le Raspberry Pi 3 B exécute ce code.
│           # Le XL1509 n'a pas de fichier (composant électrique sans programmation).
│
└── tests/                               # 🧪 TESTS UNITAIRES
    ├── __init__.py
    │
    ├── test_models/
    │   └── test_SystemData.py           # Vérifie l'enregistrement des données
    │
    ├── test_controllers/                # 🧠 TESTS DU CERVEAU (avec Mocks matériels)
    │   ├── test_ControleurVoiture.py
    │   └── test_GestionSecurite.py
    │
    └── test_materiel/                   # ⚙️ TESTS DES COMPOSANTS
        ├── test_PiloteMoteur.py         # Tests limites (ex: PWM < seuil)
        ├── test_PiloteServo.py          # Tests limites (ex: angle > 180)
        ├── test_Ultrason_HCSR04.py      # Tests limites (ex: timeout > 30ms)
        ├── test_SuiveurLigne.py         # Tests limites (ex: tous capteurs blanc)
        ├── test_CapteurCouleur.py       # Tests limites (ex: saturation lumière)
        └── test_Telemetrie.py           # Tests mesures électriques
```

