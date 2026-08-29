import os
import secrets

from fastapi import HTTPException

from dao.player_dao import PlayerDao
from utils.log_utils import log


class GameService:
    """Service that manages games."""

    @log
    def play(self, id_player: int, id_opponent: int, choice="heads"):
        """Executes a single round of a coin-flip game between two players.
        Args:
            id_player (int): The unique identifier of the first player.
            id_opponent (int): The unique identifier of the opponent.
            choice (str, optional): The player's choice ('heads' or 'tails'). Defaults to "heads".
        Returns:
            dict: A dictionary containing the match details and new elo
        Raises:
            HTTPException: 400 if the two players are the same.
            HTTPException: 404 if one or both players are not found in the database.
        """
        if id_player == id_opponent:
            raise HTTPException(status_code=400, detail="Two different players required")

        p1 = PlayerDao().find_by_id(id_player)
        p2 = PlayerDao().find_by_id(id_opponent)

        if not p1 or not p2:
            raise HTTPException(status_code=404, detail="Player not found")

        result = secrets.choice(["heads", "tails"])
        winner = p1 if result == choice else p2

        self.update_player_ratings(p1, p2, winner)

        PlayerDao().update(p1)
        PlayerDao().update(p2)

        return {
            "player1": p1.username,
            "player2": p2.username,
            "description": result,
            "winner": winner.username,
            "new_elo1": p1.elo,
            "new_elo2": p2.elo,
        }

    @classmethod
    def calculate_expected_score(cls, elo_a, elo_b) -> float:
        """Calculates the probability of player A winning against player B.
        Args:
            elo_a (float): The current Elo rating of first player.
            elo_b (float): The current Elo rating of second player.

        Returns:
            float: The expected score for player 1 (between 0 and 1).
        """
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

    @classmethod
    def calculate_new_ratings(cls, elo_a, elo_b, player_a_won: bool) -> tuple[int, int]:
        """Computes the new Elo ratings for two players after a match.
        Args:
            elo_a (float): Current Elo of player 1.
            elo_b (float): Current Elo of player 2.
            player_a_won (bool): True if player 1 won, False if player 2 won.
        Returns:
            tuple[int, int]: A tuple containing (new_elo1, new_elo2).
        """
        k_factor = int(os.environ["ELO_K_FACTOR"])

        score_a = 1.0 if player_a_won else 0.0
        score_b = 1.0 - score_a

        new_elo_a = round(elo_a + k_factor * (score_a - cls.calculate_expected_score(elo_a, elo_b)))
        new_elo_b = round(elo_b + k_factor * (score_b - cls.calculate_expected_score(elo_b, elo_a)))

        return new_elo_a, new_elo_b

    @classmethod
    def update_player_ratings(cls, p1, p2, winner):
        """Calculates and updates the elo attributes of the players.
        No update if there is no winner (Draw).
        """
        if not winner:
            return

        p1.elo, p2.elo = cls.calculate_new_ratings(p1.elo, p2.elo, player_a_won=(p1 == winner))