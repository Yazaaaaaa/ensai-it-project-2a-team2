class Alert:
    """Business object that represents an alert"""

    def __init__(
        self,
        id=None,
        user_id=None,
        neo_id=None,
        min_size_m=None,
        max_distance_km=None,
        threshold_km=None,
        is_active=True,
        created_at=None,
    ):
        self.id = id
        self.user_id = user_id
        self.neo_id = neo_id
        self.min_size_m = min_size_m
        self.max_distance_km = max_distance_km
        self.threshold_km = threshold_km
        self.is_active = is_active
        self.created_at = created_at