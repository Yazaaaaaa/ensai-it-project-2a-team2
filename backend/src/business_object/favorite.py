from datetime import datetime


class Favorite:
    """Business object representing a NEO added to a user's favorites."""

    def __init__(
        self,
        user_id: int,
        neo_id: int,
        added_at: datetime = None,
        id: int = None,
    ):
        self.id = id
        self.user_id = user_id
        self.neo_id = neo_id
        self.added_at = added_at

    def __str__(self):
        return f"Favorite({self.id}: user {self.user_id} -> neo {self.neo_id})"
