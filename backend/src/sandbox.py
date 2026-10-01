import sys
import os
import time
from dotenv import load_dotenv

# Charger le .env
load_dotenv()

# Ajouter src au chemin Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from client.nasa_client import NasaClient
from dao.neo_dao import NeoDao

def sync_all_database():
    client = NasaClient()
    dao = NeoDao()

    size = 50  # Vous pouvez augmenter la taille par page (ex: 50 ou 100) pour aller plus vite
    total_pages = 3126  # D'après vos chiffres
    
    total_inserted = 0

    print("Début de la synchronisation globale des astéroïdes...")

    # Pour un test, vous pouvez restreindre l'intervalle, ex: range(0, 5)
    # Pour tout récupérer : range(total_pages)
    for page in range (total_pages): 
        print(f"Traitement de la page {page}/{total_pages}...")
        neos = client.get_neos_page(page=page, size=size)
        
        if not neos:
            print(f"Aucun astéroïde trouvé sur la page {page}, passage à la suivante.")
            continue

        for neo in neos:
            try:
                dao.create(neo)
                total_inserted += 1
            except Exception as e:
                print(f"Erreur lors de l'insertion de l'astéroïde {neo.nasa_id}: {e}")

        # Petite pause pour éviter de saturer l'API de la NASA
        time.sleep(0.2)

    print(f"Synchronisation terminée ! {total_inserted} astéroïdes insérés ou mis à jour.")

if __name__ == "__main__":
    sync_all_database()