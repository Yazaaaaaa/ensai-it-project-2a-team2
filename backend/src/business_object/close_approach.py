class CloseApproach:
    """Business object representing a close approach event of an NEO."""

    def __init__(
        self,
        id_neo: int,
        approach_date: str,
        orbiting_body: str = None ,
        miss_distance_km: float = None,
        relative_velocity_kmh: float = None,
        id_approach: int = None,
    ):
        self.id_approach = id_approach
        self.id_neo = id_neo
        self.approach_date = approach_date
        self.orbiting_body = orbiting_body
        self.miss_distance_km = miss_distance_km
        self.relative_velocity_kmh = relative_velocity_kmh

    def __str__(self):
        return f"CloseApproach(Neo ID: {self.id_neo}, Date: {self.approach_date}, Body: {self.orbiting_body}, Dist: {self.miss_distance_km} km)"