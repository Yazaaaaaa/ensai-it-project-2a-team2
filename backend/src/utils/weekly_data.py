import sys
import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from service.neo_service import NeoService


def sync_weekly_feed(end: date | None = None):
    # Fenêtre de 7 jours maximum (l'API limite à 7 jours)
    end = end or date.today()
    start = end - timedelta(days=6)

    print(f"Synchronisation du feed du {start} au {end}...")

    result = NeoService().sync_nasa_data(start.isoformat(), end.isoformat())

    print(
        f"Terminé ! {result['synchronized_neos']} astéroïdes traités, "
        f"{result['synchronized_approaches']} nouvelles approches insérées, "
        f"{result['errors']} erreurs."
    )


if __name__ == "__main__":
    sync_weekly_feed()