import os
from pathlib import Path
from unittest import mock

import dotenv

from dao.db_connection import DBConnection
from dao.user_dao import UserDao
from utils.log_utils import get_logger, log
from utils.security import hash_password
from utils.singleton import Singleton

logger = get_logger(__name__)


class ResetDatabase(metaclass=Singleton):
    """
    Database reset utility
    """

    def __init__(self):
        # On pointe directement sur le dossier "backend"
        # reset_database.py est dans backend/src/utils/ -> on remonte de 3 niveaux
        self.base_path = Path(__file__).resolve().parent.parent.parent

    @log
    def run(self, test_dao=False):
        """Run the database reset
        If test_dao=True: reset test data
        """
        if test_dao:
            mock.patch.dict(os.environ, {"POSTGRES_SCHEMA": "project_test_dao"}).start()
            pop_data_path = self.base_path / "data" / "pop_db_test.sql"
        else:
            pop_data_path = self.base_path / "data" / "pop_db.sql"

        init_db_path = self.base_path / "data" / "init_db.sql"

        dotenv.load_dotenv()

        schema = os.environ.get("POSTGRES_SCHEMA", "project_test_dao" if test_dao else "neow")
        create_schema = f"DROP SCHEMA IF EXISTS {schema} CASCADE; CREATE SCHEMA {schema};"

        try:
            with open(init_db_path, encoding="utf-8") as init_db_file:
                init_db_as_string = init_db_file.read()

            # Si ton fichier pop_db optionnel n'existe pas, on gère le cas pour ne pas faire tout planter
            pop_db_as_string = ""
            if pop_data_path.exists():
                with open(pop_data_path, encoding="utf-8") as pop_db_file:
                    pop_db_as_string = pop_db_file.read()
            else:
                logger.warning(f"Fichier de peuplement introuvable : {pop_data_path}, on continue sans.")

        except FileNotFoundError as e:
            logger.error(f"Erreur de chemin : impossible de trouver le fichier {e.filename}")
            raise

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(create_schema)
                    cursor.execute(init_db_as_string)
                    if pop_db_as_string:
                        cursor.execute(pop_db_as_string)
        except Exception as e:
            logger.info(e)
            raise

        # Optionnel : Si tu veux hasher les mots de passe des utilisateurs créés par défaut dans les scripts SQL
        try:
            for user in UserDao().find_all():
                if user.password_hash and not user.password_hash.startswith("$2b$"): # évite de re-hasher si déjà fait
                    user.password_hash = hash_password(user.password_hash)
                    UserDao().update(user)
        except Exception as e:
            logger.info(f"Pas d'utilisateurs à mettre à jour ou table vide : {e}")

        return True


if __name__ == "__main__":
    ResetDatabase().run()
    ResetDatabase().run(True)