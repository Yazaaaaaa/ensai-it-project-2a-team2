# ENSAI IT Project — 2A Équipe 2 : NEO-Watch ☄️

> **URL de l'API :** [https://www.neowsapp.com/swagger-ui/index.html#/](https://www.neowsapp.com/swagger-ui/index.html#/)  
> **Projet :** NEO-Watch  
> **Tuteur :** Olivier Ricciardi  
> **Objectif :** Suivre et surveiller les objets géocroiseurs (*Near-Earth Objects* / NEOs) répertoriés par la NASA pour anticiper les risques d'impact et informer les utilisateurs.

---

## 🏗️ Structure du dépôt

```text
ensai-it-project-2a-team2/
├── .github/
│   └── workflows/
│       └── ci.yml             # Workflow d'intégration continue (GitHub Actions)
├── .vscode/
│   └── settings.json          # Configuration VSCode spécifique au projet
├── backend/                   # API FastAPI & Logique métier (architecture en couches)
├── frontend/                  # Interface utilisateur Streamlit (tableau de bord, recherche)
├── doc/                       # Diagrammes UML, rapport, suivi de projet
├── data/                      # Scripts SQL (création des tables et données d'initialisation)
├── .gitignore                 # Fichiers et dossiers ignorés par Git
├── docker-compose.yml         # Orchestration des conteneurs
├── LICENSE                    # Licence logicielle et droits d'utilisation
└── README.md                  # Documentation du projet
```

---

## 📁 Organisation des fichiers et dossiers

### 1. Racine du projet

| Fichier / Dossier | Description |
| :--- | :--- |
| `README.md` | Présentation du projet NEO-Watch, instructions d'installation et guide d'utilisation. |
| `LICENSE` | Précise les droits d'utilisation et la licence logicielle du dépôt. |
| `docker-compose.yml` | Configuration Docker multi-conteneurs orchestrant l'API, l'IHM et la BDD PostgreSQL. |
| `.gitignore` | Fichiers et dossiers ignorés par le suivi Git. |
| `.github/workflows/ci.yml` | Pipeline CI automatisé (tests unitaires `pytest`, analyse du code `pylint`). |
| `.vscode/settings.json` | Paramètres d'environnement VSCode partagés par l'équipe. |

---

### 2. `backend/` — Couche API (Architecture en couches)

Le backend gère la sécurité, la persistance dans PostgreSQL, la logique de surveillance des astéroïdes et la communication avec les API de la NASA (`NeoWs`, `APOD`).

```text
backend/
├── Dockerfile                 # Image Docker du backend FastAPI
├── pyproject.toml             # Configuration du projet et dépendances
├── uv.lock                    # Fichier de verrouillage des versions
├── test/                      # Tests automatisés (pytest)
│   ├── test_neo_service.py
│   ├── test_alert_service.py
│   └── test_auth_service.py
└── src/
    ├── main.py                # Point d'entrée de l'application FastAPI
    ├── controller/            # Contrôleurs HTTP (endpoints API)
    ├── service/               # Logique métier et calculs
    ├── dao/                   # Data Access Objects (requêtes SQL directes)
    ├── schema/                # Schémas de validation Pydantic
    ├── business_object/       # Entités et objets du domaine
    └── utils/                 # Outils utilitaires et sécurité
```

#### Exemples de fichiers par sous-dossier backend :

* **`src/controller/` (Routes HTTP)**  
  * `auth_controller.py` : Connexion et inscription (`F1`).
  * `neo_controller.py` : Recherche, ajout manuel et comparaison de NEOs (`F3`, `F4`, `FO1`).
  * `alert_controller.py` : Création et gestion des alertes (`F6`).
  * `admin_controller.py` : Gestion des utilisateurs, historique et rechargement NASA (`F1`, `FO2`, `FO7`).
  * `apod_controller.py` : Récupération et export de l'image du jour NASA (`FO8`).
* **`src/service/` (Logique Métier)**  
  * `neo_service.py` : Synchronisation NASA NeoWs sans écraser les ajouts manuels (`F4`).
  * `alert_service.py` : Évaluation des critères d'alerte (taille, distance, vitesse) (`F6`).
  * `stats_service.py` : Calculs statistiques sur les approches et distributions (`FO3`).
  * `recommendation_service.py` : Moteur de sélection des astéroïdes d'intérêt (`FO4`).
  * `notification_service.py` : Envoi d'emails de notification (`FO5`).
* **`src/dao/` (Accès PostgreSQL)**  
  * `db_connection.py` : Gestion de la connexion PostgreSQL.
  * `user_dao.py` : Opérations SQL sur la table des utilisateurs (`F1`).
  * `favorite_dao.py` : Persistance et historique des favoris (`F5`).
  * `search_history_dao.py` : Sauvegarde des recherches utilisateur sur 30 jours (`FO2`).
  * `modification_proposal_dao.py` : Stockage des demandes de modification (`FO6`).
* **`src/schema/` (Validation Pydantic)**  
  * `user_schema.py` : Validation des identifiants et rôles.
  * `neo_schema.py` : Structure de validation pour le filtrage et la création de NEO.
  * `alert_schema.py` : Validation des seuils de distance et taille.
* **`src/business_object/` (Entités Métier)**  
  * `user.py` : Représentation d'un utilisateur (rôles `User` / `Admin`).
  * `neo.py` : Modèle de données d'un astéroïde (nom, dimensions, dangerosité).
  * `approach.py` : Données d'approche (date, vitesse, distance de la Terre).
  * `alert.py` : Entité d'une alerte personnalisée.
* **`src/utils/` (Utilitaires)**  
  * `security.py` : Hachage des mots de passe et génération de tokens JWT.
  * `nasa_api_client.py` : Client HTTP pour interroger l'API externe NeoWs.
  * `database_reset.py` : Outil de réinitialisation de la BDD.

---

### 3. `frontend/` — Interface Graphique (Streamlit)

Interface web interactive développée en Python avec Streamlit.

```text
frontend/
├── .streamlit/
│   └── config.toml            # Thème et configuration visuelle
└── src/
    ├── app.py                 # Point d'entrée Streamlit & navigation
    ├── pages/                 # Vues applicatives
    └── utils/                 # Modules d'appui client
```

#### Exemples de fichiers par sous-dossier frontend :

* **`src/pages/` (Vues de l'application)**  
  * `dashboard.py` : Tableau de bord personnalisé (proches passages, favoris, alertes) (`F2`).
  * `search_catalog.py` : Catalogue de recherche avec filtres et exports (`F3`).
  * `add_observation.py` : Formulaire d'ajout et de proposition de modification de NEO (`F4`, `FO6`).
  * `favorites.py` : Visualisation des favoris et graphiques d'évolution des distances (`F5`).
  * `alert_settings.py` : Configuration des alertes et affichage des notifications (`F6`).
  * `comparator.py` : Outil de comparaison visuelle et tableaux de bord statistiques (`FO1`, `FO3`).
  * `admin_panel.py` : Console d'administration (comptes, historique, rechargement NASA) (`F1`, `FO2`, `FO7`).
* **`src/utils/` (Utilitaires frontend)**  
  * `api_client.py` : Encapsulation des requêtes HTTP vers l'API FastAPI backend.
  * `auth_guard.py` : Contrôle d'accès et vérification de la session utilisateur/admin.
  * `env_variables.py` : Chargement des URL et configurations d'environnement client.

---

### 4. `doc/` — Documentation du Projet

Ressources explicatives, schémas de conception et suivi de projet.

* `rapport_projet.pdf` : Rapport final du projet.
* `gantt_diagram.md` : Planning prévisionnel et jalons de livraison.
* `use_case_diagram.png` / `class_diagram.png` : Diagrammes UML fonctionnels et structures de classes.
* `activity_diagram.html` : Diagramme d'activité interactif pour la synchronisation NASA.
* `tracking/` : Dossier contenant les comptes-rendus de réunions hebdomadaires et tableaux de tâches.

---

### 5. `data/` — Données & Base de données PostgreSQL

Fichiers d'initialisation et de structure de la base PostgreSQL.

* `create_tables.sql` : Script DDL de création des tables (`users`, `neos`, `approaches`, `favorites`, `alerts`, `search_history`).
* `seed_data.sql` : Script d'insertion des données de départ (administrateur par défaut, utilisateurs de test, catalogue initial de NEOs).

---

## ⚙️ Intégration Continue (CI)

Le fichier `.github/workflows/ci.yml` définit la pipeline automatique exécutée à chaque `push` :

1. **Création du conteneur :** Instanciation d'un environnement virtuel basé sur Ubuntu (Linux).
2. **Setup environnement :** Installation de Python et des dépendances (`uv` / `pip`).
3. **Tests automatisés :** Exécution des tests unitaires `pytest` (couche `service`).
4. **Analyse de code :** Contrôle de qualité avec `pylint` (échec du pipeline si le score est sous 7.5).

*L'avancement du build est directement suivi via l'onglet **Actions** du dépôt GitHub.*

---

## 🚀 Lancement rapide avec Docker

### Prérequis
Avoir **Docker Desktop** installé et démarré.

### Définitions
* **Dockerfile :** Fichier de recettes décrivant l'environnement d'exécution de l'application backend.
* **Docker Compose :** Fichier YAML d'orchestration permettant de démarrer le backend, le frontend et la base PostgreSQL dans un réseau virtuel unifié.

### Commandes usuelles

```bash
# Lancer et construire l'ensemble des conteneurs en arrière-plan
docker compose up --build -d

# Vérifier l'état des conteneurs en cours d'exécution
docker compose ps

# Consulter les logs de tous les conteneurs
docker compose logs -f

# Consulter uniquement les logs du backend
docker compose logs -f backend

# Stopper les conteneurs sans les supprimer
docker compose stop

# Arrêter et supprimer l'ensemble des conteneurs et réseaux
docker compose down
```

### URLs d'accès aux services

* **Frontend UI (Streamlit) :** [http://localhost:8000](http://localhost:8000)
* **Backend API (FastAPI / Swagger) :** [http://localhost:5000](http://localhost:5000)
