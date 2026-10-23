1. Recherches simples (1 seul filtre)
Vous pouvez effectuer une recherche ciblée sur un seul attribut :

Par date d'approche (approach_date) : Trouver les astéroïdes qui croisent la trajectoire d'un corps à une date précise (ex: 2026-10-15).

Par identifiant NASA (nasa_id) : Retrouver un astéroïde exact par son identifiant officiel.

Par nom (name) : Rechercher une partie du nom (ex: "eros", "apophis").

Par statut de dangerosité (is_hazardous) : Filtrer uniquement les astéroïdes potentiellement dangereux (true ou false).

Par créateur (user_id) : Lister les astéroïdes personnalisés ajoutés par un utilisateur spécifique.

Par corps céleste survolé (orbiting_body) : Filtrer par planète/corps d'approche (ex: 'Earth', 'Mars').

Par taille / diamètre (min_diameter_m, max_diameter_m) : Filtrer les astéroïdes par une borne minimale ou maximale de leur diamètre moyen en mètres.

Par luminosité / magnitude (max_magnitude) : Retrouver les objets sous un certain seuil de magnitude absolue.

2. Recherches combinées (combinaisons AND)
Tous les critères peuvent être cumulés dans la même requête. Seuls les astéroïdes répondant à tous les critères fournis en même temps seront renvoyés :

Alerte d'approche dangereuse imminente :

approach_date=2026-10-15 + is_hazardous=true + orbiting_body=Earth

(Trouve les astéroïdes dangereux passant près de la Terre à une date précise)

Gros astéroïdes croisant une planète :

orbiting_body=Mars + min_diameter_m=500

(Trouve les astéroïdes de plus de 500 mètres de diamètre volant près de Mars)

Recherche personnalisée par nom et taille :

name=apollo + max_magnitude=20.0 + max_diameter_m=1000

(Trouve les astéroïdes contenant "apollo", avec une magnitude maximale de 20 et faisant moins de 1 km)

Objets d'un utilisateur à une date donnée :

user_id=7 + approach_date=2026-10-15

(Trouve les astéroïdes créés par l'utilisateur 7 prévus pour cette date)