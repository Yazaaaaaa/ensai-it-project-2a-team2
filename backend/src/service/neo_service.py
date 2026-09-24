from client.nasa_client import NasaClient
from dao.neo_dao import NeoDao
from utils.log_utils import log


class NeoService:
    """Service that manages NEO synchronization."""

    @log
    def sync_nasa_data(self, start_date: str, end_date: str) -> dict:
        """
        Fetches NEOs from the NASA client and saves them into the database.
        
        Args:
            start_date (str): Start date (YYYY-MM-DD).
            end_date (str): End date (YYYY-MM-DD).
            
        Returns:
            dict: Summary of synchronization results.
        """
        client = NasaClient()
        dao = NeoDao()

        neos = client.get_neos(start_date, end_date)
        count = 0

        for neo in neos:
            dao.create(neo)
            count += 1

        return {"status": "success", "synchronized_count": count}