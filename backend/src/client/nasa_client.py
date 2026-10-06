import os
import requests
from business_object.neo import Neo
from business_object.close_approach import CloseApproach


class NasaClient:
    """Client responsible for fetching NEO data from the NASA external API."""

    def __init__(self):
        self.api_key = os.getenv("NASA_API_KEY")
        self.browse_url = "https://api.nasa.gov/neo/rest/v1/neo/browse"
        self.feed_url = "https://api.nasa.gov/neo/rest/v1/feed"

    def get_neos_page(self, page: int = 0, size: int = 20) -> list[Neo]:
        """
        Récupère une page spécifique d'astéroïdes via l'endpoint /browse.
        
        Args:
            page (int): Numéro de la page (commence à 0).
            size (int): Nombre d'éléments par page.
            
        Returns:
            list[Neo]: Liste d'objets Neo convertis avec leurs approches multiples.
        """
        params = {
            "page": page,
            "size": size,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.browse_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            neo_list = data.get("near_earth_objects", [])
            neos = []

            for item in neo_list:
                # Extraction des diamètres en mètres
                diameter_data = item.get("estimated_diameter", {}).get("meters", {})
                diam_min = diameter_data.get("estimated_diameter_min")
                diam_max = diameter_data.get("estimated_diameter_max")

                # Extraction de TOUTES les données d'approche (close_approach_data)
                approach_data_list = item.get("close_approach_data", [])
                close_approaches = []

                for approach_item in approach_data_list:
                    app_date = approach_item.get("close_approach_date")
                    orbiting_body = approach_item.get("orbiting_body")
                    
                    miss_distance_km = None
                    miss_dist_str = approach_item.get("miss_distance", {}).get("kilometers")
                    if miss_dist_str:
                        miss_distance_km = float(miss_dist_str)

                    relative_velocity_kmh = None
                    vel_str = approach_item.get("relative_velocity", {}).get("kilometers_per_hour")
                    if vel_str:
                        relative_velocity_kmh = float(vel_str)

                    # Instanciation directe de l'objet CloseApproach (id_neo sera assigné lors de l'insertion)
                    close_approaches.append(
                        CloseApproach(
                            id_neo=None,
                            approach_date=app_date,
                            orbiting_body=orbiting_body,
                            miss_distance_km=miss_distance_km,
                            relative_velocity_kmh=relative_velocity_kmh
                        )
                    )

                # Instanciation correspondant au nouveau Business Object Neo
                neo = Neo(
                    nasa_id=str(item.get("id")),
                    name_neo=item.get("name"),
                    diameter_min_m=diam_min,
                    diameter_max_m=diam_max,
                    absolute_magnitude=item.get("absolute_magnitude_h"),
                    is_hazardous=item.get("is_potentially_hazardous_asteroid", False),
                    is_custom=False
                )
                
                # On attache la liste complète des objets CloseApproach à l'objet Neo
                neo.close_approaches = close_approaches
                neos.append(neo)

            return neos

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return []

    def get_weekly_feed(self, start_date: str, end_date: str) -> list[Neo]:
        """
        Récupère les astéroïdes via l'endpoint /feed pour une période donnée (max 7 jours).
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.feed_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            neos_data = data.get("near_earth_objects", {})
            neos = []

            for date_str, neo_list in neos_data.items():
                for item in neo_list:
                    diameter_data = item.get("estimated_diameter", {}).get("meters", {})
                    diam_min = diameter_data.get("estimated_diameter_min")
                    diam_max = diameter_data.get("estimated_diameter_max")

                    approach_data_list = item.get("close_approach_data", [])
                    close_approaches = []

                    for approach_item in approach_data_list:
                        app_date = approach_item.get("close_approach_date")
                        orbiting_body = approach_item.get("orbiting_body")
                        
                        miss_distance_km = None
                        miss_dist_str = approach_item.get("miss_distance", {}).get("kilometers")
                        if miss_dist_str:
                            miss_distance_km = float(miss_dist_str)

                        relative_velocity_kmh = None
                        vel_str = approach_item.get("relative_velocity", {}).get("kilometers_per_hour")
                        if vel_str:
                            relative_velocity_kmh = float(vel_str)

                        close_approaches.append(
                            CloseApproach(
                                id_neo=None,
                                approach_date=app_date,
                                orbiting_body=orbiting_body,
                                miss_distance_km=miss_distance_km,
                                relative_velocity_kmh=relative_velocity_kmh
                            )
                        )

                    neo = Neo(
                        nasa_id=str(item.get("id")),
                        name_neo=item.get("name"),
                        diameter_min_m=diam_min,
                        diameter_max_m=diam_max,
                        absolute_magnitude=item.get("absolute_magnitude_h"),
                        is_hazardous=item.get("is_potentially_hazardous_asteroid", False),
                        is_custom=False
                    )
                    
                    neo.close_approaches = close_approaches

                    if not any(n.nasa_id == neo.nasa_id for n in neos):
                        neos.append(neo)

            return neos

        except requests.exceptions.RequestException as e:
            print(f"Error fetching weekly feed from {start_date} to {end_date}: {e}")
            return []