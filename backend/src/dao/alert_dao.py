from business_object.game import Game
from dao.db_connection import DBConnection
from dao.player_dao import PlayerDao
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class GameDao(metaclass=Singleton):
    """Class containing methods to access Games in the database."""

    @log
    def create(self, game: Game) -> bool:
        """
        Inserts a new game record.
        Args:
            game (Game): The game object to persist.
        Returns:
            bool: True if insertion is successful, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO game (id_player1, id_player2, game_mode, id_winner, detail) "
                        "VALUES (%(id_p1)s, %(id_p2)s, %(mode)s, %(id_w)s, %(detail)s) "
                        "RETURNING id_game;",
                        {
                            "id_p1": game.player1.id_player,
                            "id_p2": game.player2.id_player,
                            "mode": game.game_mode,
                            "id_w": game.winner.id_player if game.winner else None,
                            "detail": game.description,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            raise

        created = False
        if res:
            game.id_game = res["id_game"]
            created = True

        return created

    @log
    def find_by_id(self, id_game: int) -> Game | None:
        """
        Retrieves a specific game and converts the database row into a Game object.
        Args:
            id_game (int): The ID of the game to find.
        Returns:
            Game: The game object if found, otherwise None.
        """
        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM game
                         WHERE id_game = %(id_game)s;
                        """,
                        {"id_game": id_game},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error finding game {id_game}: {e}")
            raise

        if not res:
            return None

        p1 = PlayerDao().find_by_id(res["id_player1"])
        p2 = PlayerDao().find_by_id(res["id_player2"])

        winner = None
        if res["id_winner"]:
            winner = PlayerDao().find_by_id(res["id_winner"])

        return Game(
            id_game=res["id_game"],
            player1=p1,
            player2=p2,
            game_mode=res["game_mode"],
            winner=winner,
            description=res["detail"],
            timestamp=res["timestamp"],
        )

    @log
    def find_all_by_player(self, id_player: int) -> list[Game]:
        """
        Returns all games involving a specific player.
        Args:
            id_player (int): The ID of the player to search for.
        Returns:
            list[Game]: A list of Game objects.
        """
        rows = []

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM game
                         WHERE id_player1 = %(id_p)s OR id_player2 = %(id_p)s
                         ORDER BY timestamp DESC;
                        """,
                        {"id_p": id_player},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding games for player {id_player}: {e}")
            raise

        games = []
        for row in rows:
            p1 = PlayerDao().find_by_id(row["id_player1"])
            p2 = PlayerDao().find_by_id(row["id_player2"])

            winner = None
            if row["id_winner"]:
                winner = PlayerDao().find_by_id(row["id_winner"])

            games.append(
                Game(
                    id_game=row["id_game"],
                    player1=p1,
                    player2=p2,
                    game_mode=row["game_mode"],
                    winner=winner,
                    description=row["detail"],
                    timestamp=row["timestamp"],
                )
            )

        return games
