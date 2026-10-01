class Neo:
    """Business object representing a Near-Earth Object (NEO)."""

    def __init__(
        self,
        nasa_id: str,
        name_neo: str,
        diameter_min_m: float = None,
        diameter_max_m: float = None,
        absolute_magnitude: float = None,
        is_hazardous: bool = False,
        is_custom: bool = False,
        created_by_user_id: int = None,
        id_neo: int = None,
    ):
        self.id_neo = id_neo
        self.nasa_id = nasa_id
        self.name_neo = name_neo
        self.diameter_min_m = diameter_min_m
        self.diameter_max_m = diameter_max_m
        self.absolute_magnitude = absolute_magnitude
        self.is_hazardous = is_hazardous
        self.is_custom = is_custom
        self.created_by_user_id = created_by_user_id

    def __str__(self):
        return f"Neo({self.nasa_id}: {self.name_neo}, Hazardous: {self.is_hazardous})"