from datetime import datetime


class Favorite:
    """Business object representing a NEO added to a user's favorites."""

    def __init__(
        self,
        id_user: int,
        neo_id: int,
        added_at: datetime = None,
        id_favorite: int = None,
    ):
        self.id_favorite = id
        self.id_user = id_user
        self.neo_id = neo_id
        self.added_at = added_at

    def __str__(self):
        return f"Favorite({self.id_favorite}: user {self.id_user} -> neo {self.neo_id})"
