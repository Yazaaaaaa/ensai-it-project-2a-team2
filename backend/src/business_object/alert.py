class Alert:
    """Business object that represents an alert"""

    def __init__(
        self,
        id=None,
        user_id=None,
        neo_id=None,
        threshold_km=None,
        threshold_size=None,
        is_active=True,
        created_at=None,
    ):
        self.id = id
        self.user_id = user_id
        self.neo_id = neo_id
        self.threshold_km = threshold_km
        self.threshold_size = threshold_size
        self.is_active = is_active
        self.created_at = created_at

    def __str__(self):
        return f"Alert({self.id}: user {self.user_id} -> neo {self.neo_id or 'any'}, < {self.threshold_km} km)"