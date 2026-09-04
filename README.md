# ENSAI IT Project — 2A Équipe 2 : NEO-Watch ☄️

URL API: https://www.neowsapp.com/swagger-ui/index.html#/

**Projet :** NEO-Watch  
**Tuteur :** Olivier Ricciardi  
**Objectif :** Suivre et surveiller les objets géocroiseurs (*Near-Earth Objects* / NEOs) répertoriés par la NASA pour anticiper les risques d'impact et informer les utilisateurs.

---

## Structure du dépôt

ensai-it-project-2a-team2/
├── .github/
│   └── workflows/
│       └── ci.yml             # Workflow d'intégration continue (GitHub Actions)
├── .vscode/
│   └── settings.json          # Configuration VSCode spécifique au projet
├── backend/                   # API FastAPI & Logique métier (architecture en couches)
├── frontend/                  # Interface utilisateur Streamlit (tableau de bord, recherche, graphiques)
├── doc/                       # Diagrammes UML, rapport, suivi de projet
├── data/                      # Scripts SQL (création des tables et données d'initialisation)
├── .gitignore                 # Fichiers et dossiers ignorés par Git
├── docker-compose.yml         # Orchestration des conteneurs
├── LICENSE                    # Licence logicielle et droits d'utilisation
└── README.md                  # Documentation du projet

---

## Organisation des fichiers et dossiers

### 1. Racine du projet

- README.md : Présentation du projet NEO-Watch, instructions d'installation et guide d'utilisation.
- LICENSE : Précise les droits d'utilisation et la licence logicielle du dépôt.
- docker-compose.yml : Configuration Docker multi-conteneurs orchestrant le backend FastAPI, l'interface Streamlit et la base PostgreSQL.
- .gitignore : Fichiers et dossiers ignorés par Git.
- .github/workflows/ci.yml : Pipeline CI automatisé (tests unitaires pytest, analyse du code Pylint).
- .vscode/settings.json : Paramètres d'environnement VSCode partagés par l'équipe.

### 2. backend/ — Couche API (Détail de l'architecture pour NEO-Watch)

Le backend gère la sécurité, la persistance dans PostgreSQL, la logique de surveillance des astéroïdes et la communication avec les API de la NASA (NeoWs, APOD). Il s'appuie sur une architecture en couches :

- Dockerfile : Fichier de build Docker pour conteneuriser l'API FastAPI.
- pyproject.toml / uv.lock : Gestionnaire de dépendances Python (uv / poetry).
- test/ : Tests automatisés exécutés via pytest (validation de la couche service et des règles de gestion).
- src/ : Code source de l'application backend.
  - main.py : Point d'entrée de l'application FastAPI ; configure l'API, les middlewares et inclut les routes.
  - controller/ : **Contrôleurs et Routes HTTP** — Reçoit les requêtes de l'utilisateur ou du frontend et renvoie les réponses HTTP.
    - Ex. : `auth_controller.py` (connexion/inscription F1), `neo_controller.py` (recherche, ajouts manuel F3/F4, comparaison FO1), `alert_controller.py` (gestion des alertes F6), `admin_controller.py` (gestion utilisateurs/historique FO2 et rechargement NASA F1/FO7), `apod_controller.py` (export de l'image du jour NASA FO8).
  - service/ : **Logique Métier & Calculs** — Contient l'intelligence de l'application.
    - Ex. : Synchronisation des données NASA NeoWs tout en préservant les NEO créés manuellement (F4), évaluation des critères d'alerte (taille, distance, vitesse F6), calcul des statistiques d'approche/distribution (FO3), moteur de recommandation d'astéroïdes d'intérêt (FO4), et génération des emails de notification (FO5).
  - dao/ (Data Access Object) : **Accès aux Données (PostgreSQL)** — Exécute les requêtes SQL directes à la base de données.
    - Ex. : Requêtes d'insertion/lecture des utilisateurs, persistance de la liste des favoris (F5), sauvegarde de l'historique des recherches sur 30 jours (FO2), stockage des propositions de modification d'amateurs (FO6) et gestion de la réinitialisation (`db_connection.py`).
  - schema/ : **Schémas de Validation (Pydantic)** — Valide le format des requêtes reçues et sérialise les réponses JSON.
    - Ex. : Modèles pour la création de compte, les filtres de recherche de NEOs, la structure d'une alerte personnalisée ou les propositions de modification.
  - business_object/ : **Entités Métier** — Représente les objets fondamentaux du domaine NEO-Watch manipulant les données métier.
    - Ex. : `User` (rôles utilisateur/admin), `NEO` (identifiant, nom, taille, vitesse, niveau de dangerosité), `Approach` (distance, date de passage), `Alert` et `SearchRecord`.
  - utils/ : **Outils Utilitaires & Sécurité** — Modules d'appui réutilisables.
    - Ex. : Hachage des mots de passe et génération de tokens JWT (`security.py`), client d'intégration avec l'API externe de la NASA (`nasa_api_client.py`), utilitaires de logs et réinitialisation de la base.

### 3. frontend/ — Interface Graphique (Streamlit)

Interface web interactive développée en Python avec Streamlit pour permettre la navigation et le suivi des géocroiseurs.

- .streamlit/config.toml : Personnalisation graphique et thématique du tableau de bord Streamlit.
- src/ : Code source de l'interface graphique.
  - app.py : Point d'entrée de l'application Streamlit et gestion du menu principal.
  - pages/ : Vues applicatives correspondant aux fonctionnalités de NEO-Watch :
    - Dashboard personnalisé (synthèse des proches passages, objets dangereux, favoris - F2)
    - Catalogue & Recherche de NEOs avec exports (F3)
    - Formulaire d'observation pour ajouter/proposer des NEOs (F4, FO6)
    - Espace Favoris avec graphiques d'évolution des distances (F5)
    - Centre de configuration des alertes et notifications (F6)
    - Comparateur visuel d'astéroïdes (FO1) & Statistiques globales (FO3)
    - Console d'administration (gestion des comptes, historique des recherches, synchronisation NASA - F1, FO2, FO7)
  - utils/ :
    - api_client.py : Module de communication HTTP avec les endpoints du backend FastAPI.
    - auth_guard.py : Contrôle d'accès sécurisant la navigation selon le rôle connecté (utilisateur / administrateur).
    - env_variables.py : Chargement des configurations d'environnement du frontend.

### 4. doc/ — Documentation du Projet

- Rapport de projet complet, suivi d'avancement (tracking hebdomadaire) et comptes-rendus de réunion.
- Diagrammes UML (diagrammes de classes, de cas d'utilisation et de séquence pour les flux d'alerte et de synchronisation NASA).
- gantt_diagram.md : Planning prévisionnel et jalons de livraison.

### 5. data/ — Données & Base de données PostgreSQL

- Scripts SQL de création du schéma de base de données PostgreSQL.
- Jeux de données d'initialisation (*seeds*) pour insérer les premiers utilisateurs, administrateurs et catalogue initial de NEOs.

---

## Intégration Continue (CI)

Le dépôt contient un fichier de workflow automatisé (`.github/workflows/ci.yml`).
Chaque push sur GitHub déclenche un pipeline qui exécute les étapes suivantes :

1. Création d'un conteneur à partir d'une image Ubuntu (Linux) (machine virtuelle avec un noyau Linux).
2. Installation de Python.
3. Installation des paquets et dépendances requis.
4. Exécution des tests unitaires (uniquement la couche service, l'exécution des tests DAO étant plus complexe).
5. Analyse du code avec Pylint (échec de l'étape si le score est inférieur à 7.5).

L'avancement du pipeline est consultable directement sur GitHub dans l'onglet **Actions**.

---

## Lancement rapide avec Docker

Prérequis : Docker Desktop installé.

- Dockerfile : Empreinte et instructions d'assemblage de l'image de l'application et de son environnement.
- Docker Compose : Outil de configuration (via fichier YAML) pour exécuter et lier les différents services (backend, frontend, BDD PostgreSQL).

### Commandes principales

- Lancer et construire les conteneurs : `docker compose up --build -d`
- Voir les processus en cours : `docker compose ps`
- Consulter les logs :
  - Tous les conteneurs : `docker compose logs -f`
  - Backend uniquement : `docker compose logs -f backend`
- Arrêter les conteneurs : `docker compose stop`
- Supprimer les conteneurs : `docker compose down`

### Accès aux services

- Backend API (FastAPI / Swagger) : http://localhost:5000
- Frontend UI (Streamlit) : http://localhost:8000