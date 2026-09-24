import sys
import os
from dotenv import load_dotenv

# Charge le .env pour remplir os.environ avec les clés du prof
load_dotenv()

# Ajoute src au chemin Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from service.neo_service import NeoService

def test_sync():
    service = NeoService()
    start_date = "2026-09-24"
    end_date = "2026-09-27"
    
    print(f"Lancement de la synchronisation du {start_date} au {end_date}...")
    result = service.sync_nasa_data(start_date, end_date)
    print("Résultat :", result)

if __name__ == "__main__":
    test_sync()