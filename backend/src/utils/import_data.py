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
from dao.close_approach_dao import CloseApproachDao

def sync_all_database():
    client = NasaClient()
    dao = NeoDao()
    approach_dao = CloseApproachDao()

    size = 20  # Nombre d'éléments par page
    total_pages = 3129  # D'après vos chiffres
    
    total_inserted = 0
    total_approaches = 0

    print("Début de la synchronisation globale des astéroïdes et de leurs approches...")

    # Pour un test rapide, vous pouvez restreindre l'intervalle, ex: range(0, 5)
    for page in range(total_pages): 
        print(f"Traitement de la page {page}/{total_pages}...")
        neos = client.get_neos_page(page=page, size=size)
        
        if not neos:
            print(f"Aucun astéroïde trouvé sur la page {page}, passage à la suivante.")
            continue

        for neo in neos:
            try:
                # 1. Insertion ou mise à jour du NEO (ce qui génère/récupère neo.id_neo)
                dao.create(neo)
                total_inserted += 1

                # 2. Insertion de tous les passages de close_approach pour ce NEO
                for approach in neo.close_approaches:
                    approach.id_neo = neo.id_neo  # On lie l'approche à l'ID de l'astéroïde
                    approach_dao.create(approach)
                    total_approaches += 1

            except Exception as e:
                print(f"Erreur lors de l'insertion de l'astéroïde {neo.nasa_id}: {e}")

        # Petite pause pour éviter de saturer l'API de la NASA
        time.sleep(0.2)

    print(f"Synchronisation terminée ! {total_inserted} astéroïdes et {total_approaches} approches traités.")

if __name__ == "__main__":
    sync_all_database()