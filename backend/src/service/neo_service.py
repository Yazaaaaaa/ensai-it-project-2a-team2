from client.nasa_client import NasaClient
from dao.neo_dao import NeoDao
from dao.close_approach_dao import CloseApproachDao
from utils.log_utils import log


class NeoService:
    """Service that manages NEO synchronization."""

    @log
    def sync_nasa_data(self, start_date: str, end_date: str) -> dict:
        """
        Fetches NEOs from the NASA client and saves them into the database, 
        along with their multiple close approaches.
        
        Args:
            start_date (str): Start date (YYYY-MM-DD).
            end_date (str): End date (YYYY-MM-DD).
            
        Returns:
            dict: Summary of synchronization results.
        """
        client = NasaClient()
        neo_dao = NeoDao()
        approach_dao = CloseApproachDao()

        # Utilisation de get_weekly_feed (puisque get_neos n'existe plus dans le client)
        neos = client.get_weekly_feed(start_date, end_date)
        neo_count = 0
        approach_count = 0

        for neo in neos:
            # 1. Insertion ou mise à jour du NEO (ce qui génère neo.id_neo)
            neo_dao.create(neo)
            neo_count += 1

            # 2. Insertion de tous les passages associés
            for approach in neo.close_approaches:
                approach.id_neo = neo.id_neo  # On lie l'approche à l'ID de l'astéroïde
                approach_dao.create(approach)
                approach_count += 1

        return {
            "status": "success",
            "synchronized_neos": neo_count,
            "synchronized_approaches": approach_count
        }