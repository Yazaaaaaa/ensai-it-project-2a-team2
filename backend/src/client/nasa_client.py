import os
import requests
from business_object.neo import Neo


class NasaClient:
    """Client responsible for fetching NEO data from the NASA external API."""

    def __init__(self):
        self.api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.nasa.gov/neo/rest/v1/feed"

    def get_neos(self, start_date: str, end_date: str) -> list[Neo]:
        """
        Fetches NEOs from the NASA API and converts them into Neo business objects.

        Args:
            start_date (str): Start date (YYYY-MM-DD).
            end_date (str): End date (YYYY-MM-DD).

        Returns:
            list[Neo]: A list of Neo objects.
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            neos_data = data.get("near_earth_objects", {})
            neos = []

            for date_str, neo_list in neos_data.items():
                for item in neo_list:
                    # Extraction des diamètres en mètres
                    diameter_data = item.get("estimated_diameter", {}).get("meters", {})
                    diam_min = diameter_data.get("estimated_diameter_min")
                    diam_max = diameter_data.get("estimated_diameter_max")

                    # Extraction des données d'approche (on prend le premier élément de la liste s'il existe)
                    approach_data_list = item.get("close_approach_data", [])
                    approach_date = None
                    miss_distance_km = None
                    relative_velocity_kmh = None

                    if approach_data_list:
                        # On cherche l'approche correspondant à la date courante ou on prend la première
                        approach_item = next(
                            (app for app in approach_data_list if app.get("close_approach_date") == date_str),
                            approach_data_list[0]
                        )

                        approach_date = approach_item.get("close_approach_date")

                        # Distance de raté en kilomètres
                        miss_distance_data = approach_item.get("miss_distance", {})
                        miss_distance_km = miss_distance_data.get("kilometers")
                        if miss_distance_km is not None:
                            miss_distance_km = float(miss_distance_km)

                        # Vitesse relative en km/h
                        velocity_data = approach_item.get("relative_velocity", {})
                        relative_velocity_kmh = velocity_data.get("kilometers_per_hour")
                        if relative_velocity_kmh is not None:
                            relative_velocity_kmh = float(relative_velocity_kmh)

                    neo = Neo(
                        nasa_id=str(item.get("id")),
                        name_neo=item.get("name"),
                        diameter_min_m=diam_min,
                        diameter_max_m=diam_max,
                        absolute_magnitude=item.get("absolute_magnitude_h"),
                        approach_date=approach_date,
                        miss_distance_km=miss_distance_km,
                        relative_velocity_kmh=relative_velocity_kmh,
                        is_hazardous=item.get("is_potentially_hazardous_asteroid", False),
                        is_custom=False
                    )

                    # Évite d'ajouter plusieurs fois le même astéroïde s'il apparaît sur plusieurs jours
                    if not any(n.nasa_id == neo.nasa_id for n in neos):
                        neos.append(neo)

            return neos

        except requests.exceptions.RequestException as e:
            print(f"Error fetching NASA NEOs: {e}")
            return []