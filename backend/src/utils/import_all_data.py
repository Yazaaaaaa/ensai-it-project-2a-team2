import sys
import os
import time
from dotenv import load_dotenv

# Charger le .env
load_dotenv()

# Ajouter src au chemin Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from service.neo_service import NeoService


def sync_all_database():
    service = NeoService()

    size = 20  # Nombre d'éléments par page
    total_pages = 3135

    total_neos = 0
    total_approaches = 0
    total_errors = 0

    print("Début de la synchronisation globale des astéroïdes et de leurs approches...")

    # Pour un test rapide, vous pouvez restreindre l'intervalle, ex: range(0, 5)
    for page in range(total_pages):
        print(f"Traitement de la page {page}/{total_pages}...")
        result = service.sync_page(page=page, size=size)

        total_neos += result["synchronized_neos"]
        total_approaches += result["synchronized_approaches"]
        total_errors += result["errors"]

        # Petite pause pour éviter de saturer l'API de la NASA
        time.sleep(0.2)

    print(
        f"Synchronisation terminée ! {total_neos} astéroïdes traités, "
        f"{total_approaches} nouvelles approches insérées, {total_errors} erreurs."
    )


if __name__ == "__main__":
    sync_all_database()