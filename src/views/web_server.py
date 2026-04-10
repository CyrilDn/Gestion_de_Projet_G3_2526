#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur Web Flask - Interface de Contrôle Voiture Groupe 3
US2: Redémarrage automatique via interface web

Ce serveur permet de:
- Afficher une page web avec un bouton de démarrage
- Lancer le script de test (ou le coeur métier par la suite)
- Être accessible via le hotspot de la voiture (http://10.42.0.1:5000)
"""

from flask import Flask, render_template, jsonify, request
import subprocess
import os
import sys
import glob
import json

app = Flask(__name__)

# Configuration
SCRIPT_TEST_PATH = "/home/user/Cars/Gestion_de_Projet_G3_2526/tests/Script_avant_course.py"
CONTROLEUR_PATH = "/home/user/Cars/Gestion_de_Projet_G3_2526/src/controllers/ControleurVoiture.py"
LOG_DIR = "/home/user/Cars/Gestion_de_Projet_G3_2526/src/models/logs"
SENSORS_FILE = "/home/user/Cars/Gestion_de_Projet_G3_2526/src/models/sensors.json"


@app.route('/')
def index():
    """
    Page d'accueil avec le bouton de démarrage
    """
    return render_template('index.html')

@app.route('/demarrer_controleur', methods=['POST'])
def demarrer_controleur():
    """
    Lance le ControleurVoiture (cœur métier)
    Retourne un JSON avec le statut
    """
    try:
        # Vérifier que le script existe
        if not os.path.exists(CONTROLEUR_PATH):
            return jsonify({
                'success': False,
                'message': f'Contrôleur introuvable: {CONTROLEUR_PATH}'
            }), 404
        
        # Lancer le contrôleur en arrière-plan
        process = subprocess.Popen(
            [sys.executable, CONTROLEUR_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return jsonify({
            'success': True,
            'message': 'ControleurVoiture démarré avec succès!',
            'pid': process.pid
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du démarrage: {str(e)}'
        }), 500

@app.route('/demarrer', methods=['POST'])
def demarrer_voiture():
    """
    Lance le script de test (ou le coeur métier)
    Retourne un JSON avec le statut
    """
    try:
        # Vérifier que le script existe
        if not os.path.exists(SCRIPT_TEST_PATH):
            return jsonify({
                'success': False,
                'message': f'Script introuvable: {SCRIPT_TEST_PATH}'
            }), 404
        
        # Lancer le script en arrière-plan
        # Utilisation de subprocess.Popen pour ne pas bloquer la réponse HTTP
        process = subprocess.Popen(
            [sys.executable, SCRIPT_TEST_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Détacher du processus Flask
        )
        
        return jsonify({
            'success': True,
            'message': 'Script de test démarré avec succès!',
            'pid': process.pid
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du démarrage: {str(e)}'
        }), 500


@app.route('/sensors')
def get_sensors():
    """
    Retourne les dernières valeurs des 3 capteurs ultrasons (fichier JSON écrit par le contrôleur).
    """
    if not os.path.exists(SENSORS_FILE):
        return jsonify({'success': False, 'message': 'Contrôleur pas encore démarré'})
    try:
        with open(SENSORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'success': True, **data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/status')
def status():
    """
    Endpoint pour vérifier que le serveur est actif
    """
    return jsonify({
        'status': 'running',
        'message': 'Serveur web actif'
    })


@app.route('/logs')
def get_logs():
    """
    Récupère le contenu complet du fichier log demandé.
    Par défaut, renvoie le fichier log le plus récent (une course = un fichier).
    """
    try:
        if not os.path.exists(LOG_DIR):
            return jsonify({
                'success': False,
                'logs': [],
                'message': f'Dossier introuvable: {LOG_DIR}'
            })

        log_files = sorted(
            glob.glob(os.path.join(LOG_DIR, '*.log')),
            key=os.path.getmtime,
            reverse=True
        )

        if not log_files:
            return jsonify({
                'success': True,
                'logs': [],
                'message': 'Aucun fichier log trouvé',
                'log_file': None,
                'available_logs': []
            })

        requested_file = request.args.get('file')
        if requested_file:
            requested_name = os.path.basename(requested_file)
            selected_log = os.path.join(LOG_DIR, requested_name)
            if not os.path.exists(selected_log):
                return jsonify({
                    'success': False,
                    'logs': [],
                    'message': f'Fichier log introuvable: {requested_name}'
                }), 404
        else:
            selected_log = log_files[0]

        log_filename = os.path.basename(selected_log)

        with open(selected_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            clean_lines = [line.rstrip('\n') for line in lines]

        return jsonify({
            'success': True,
            'logs': clean_lines,
            'log_file': log_filename,
            'total_lines': len(clean_lines),
            'displayed_lines': len(clean_lines),
            'available_logs': [os.path.basename(path) for path in log_files]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'logs': [],
            'message': f'Erreur: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚗 Serveur Web Voiture Groupe 3 - Démarrage")
    print("=" * 60)
    print(f"📍 Accès: http://10.42.0.1:5000")
    print(f"📜 Script à lancer: {SCRIPT_TEST_PATH}")
    print("=" * 60)
    
    # Lancer le serveur Flask
    # host='0.0.0.0' permet l'accès depuis n'importe quelle IP (notamment le hotspot)
    # port=5000 est le port par défaut
    # debug=False en production (mettre True pour le développement)
    app.run(host='0.0.0.0', port=5000, debug=False)