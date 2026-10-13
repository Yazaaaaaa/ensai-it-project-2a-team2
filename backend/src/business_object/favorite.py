from datetime import datetime


class Favorite:
    """Business object representing a NEO added to a user's favorites."""

    def __init__(
        self,
        id_user: int,
        id_neo: int,
        added_at: datetime = None,
        id_favorite: int = None,
    ):
        self.id_favorite = id
        self.id_user = id_user
        self.id_neo = id_neo
        self.added_at = added_at

    def __str__(self):
        return f"Favorite({self.id_favorite}: user {self.id_user} -> neo {self.id_neo})"
