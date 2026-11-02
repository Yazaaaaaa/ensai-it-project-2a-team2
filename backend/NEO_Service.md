## Rechercher des NEOs

### Prérequis

Lancer l'API depuis la racine du dépôt :

```bash
uv sync --project backend --all-extras
uv run --project backend python backend/src/main.py
```

L'API écoute sur `http://localhost:5000`. Les commandes ci-dessous sont à lancer dans un second terminal.
La route de recherche est `GET /neo`, et les filtres se passent en paramètres d'URL
(après `?`, séparés par `&`). **Les URL contenant `&` doivent être entre guillemets.**

### 1. Recherches simples (1 seul filtre)

| Filtre | Description | Commande |
|---|---|---|
| `nasa_id` | Identifiant NASA exact | `curl "http://localhost:5000/neo?nasa_id=2000433"` |
| `name` | Partie du nom, sans tenir compte de la casse | `curl "http://localhost:5000/neo?name=eros"` |
| `is_hazardous` | Potentiellement dangereux (`true` / `false`) | `curl "http://localhost:5000/neo?is_hazardous=true"` |
| `user_id` | NEOs personnalisés créés par un utilisateur | `curl "http://localhost:5000/neo?user_id=7"` |
| `orbiting_body` | Corps survolé lors d'une approche (casse respectée : `Earth`, `Mars`) | `curl "http://localhost:5000/neo?orbiting_body=Earth"` |
| `min_diameter_m` | Diamètre moyen minimal, en mètres | `curl "http://localhost:5000/neo?min_diameter_m=140"` |
| `max_diameter_m` | Diamètre moyen maximal, en mètres | `curl "http://localhost:5000/neo?max_diameter_m=1000"` |
| `max_magnitude` | Magnitude absolue maximale | `curl "http://localhost:5000/neo?max_magnitude=22"` |

Les NEOs dont le diamètre ou la magnitude est inconnu sont exclus dès qu'un de ces filtres est utilisé.

Si une valeur contient des espaces ou des parenthèses (par exemple un nom complet), laisser `curl` l'encoder :

```bash
curl -G "http://localhost:5000/neo" --data-urlencode "name=2063 Bacchus (1977 HB)"
```

### 2. Recherches combinées (ET logique)

Tous les filtres peuvent être cumulés : seuls les NEOs qui respectent **tous** les critères sont renvoyés.

**Dangereux passant près de la Terre**
```bash
curl "http://localhost:5000/neo?orbiting_body=Earth&is_hazardous=true"
```

**Gros astéroïdes (plus de 500 m) passant près de Mars**
```bash
curl "http://localhost:5000/neo?orbiting_body=Mars&min_diameter_m=500"
```

**Nom contenant « apollo », magnitude ≤ 20 et diamètre ≤ 1 km**
```bash
curl "http://localhost:5000/neo?name=apollo&max_magnitude=20.0&max_diameter_m=1000"
```

**NEOs dangereux de plus de 140 m et de magnitude ≤ 22 (définition NASA d'un PHA)**
```bash
curl "http://localhost:5000/neo?is_hazardous=true&min_diameter_m=140&max_magnitude=22"
```

**NEOs non dangereux créés par l'utilisateur 7**
```bash
curl "http://localhost:5000/neo?user_id=7&is_hazardous=false"
```

### 3. Trier les résultats

Ajouter `sort_by` (`name`, `diameter`, `magnitude` ou `hazardous`) et, si besoin, `descending=true` :

```bash
curl "http://localhost:5000/neo?orbiting_body=Earth&is_hazardous=true&sort_by=diameter&descending=true"
```

Les NEOs dont la valeur de tri est inconnue sont placés en fin de liste.

### 4. Lire plus facilement le résultat

```bash
# JSON mis en forme
curl -s "http://localhost:5000/neo?is_hazardous=true" | python -m json.tool

# Nombre de résultats
curl -s "http://localhost:5000/neo?is_hazardous=true" | python -c "import sys, json; print(len(json.load(sys.stdin)))"
```