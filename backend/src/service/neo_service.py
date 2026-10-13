from client.nasa_client import NasaClient
from dao.neo_dao import NeoDao
from dao.close_approach_dao import CloseApproachDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class NeoService:
    """Service that manages NEO synchronization."""

    @log
    def sync_nasa_data(self, start_date: str, end_date: str) -> dict:
        """Synchronizes the NEOs of a date window (max 7 days) via the /feed endpoint."""
        neos = NasaClient().get_weekly_feed(start_date, end_date)
        return self._save_neos(neos)

    @log
    def sync_page(self, page: int, size: int = 20) -> dict:
        """Synchronizes one page of the full NASA catalog via the /browse endpoint."""
        neos = NasaClient().get_neos_page(page=page, size=size)
        return self._save_neos(neos)

    def _save_neos(self, neos: list) -> dict:
        """Saves NEOs and their close approaches, and returns a summary."""
        neo_dao = NeoDao()
        approach_dao = CloseApproachDao()

        neo_count = 0
        approach_count = 0
        error_count = 0

        for neo in neos:
            try:
                # 1. Insertion ou mise à jour du NEO (renseigne neo.id_neo)
                neo_dao.create(neo)
                neo_count += 1

                # 2. Insertion des approches (celles déjà présentes sont ignorées)
                for approach in neo.close_approaches:
                    approach.id_neo = neo.id_neo
                    if approach_dao.create(approach):
                        approach_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error synchronizing NEO {neo.nasa_id}: {e}")

        return {
            "status": "success",
            "synchronized_neos": neo_count,
            "synchronized_approaches": approach_count,
            "errors": error_count
        }