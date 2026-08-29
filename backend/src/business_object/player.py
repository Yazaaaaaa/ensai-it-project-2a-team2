class Player:
    """
    Class representing a Player.
    Attributes:
        id_player (int): The unique identifier for the player.
        username (str): The player's username.
        password (str): The player's password.
        elo (int): The player's Elo rating.
        email (str): The player's email address.
        pokemon_fan (bool): Indicates whether the player is a Pokémon fan.
        access_token (str, optional): The authentication token for the player.
    """

    def __init__(
        self,
        username,
        elo,
        email,
        password=None,
        pokemon_fan=False,
        id_player=None,
        access_token=None,
    ):
        """Constructor"""
        self.id_player = id_player
        self.username = username
        self.password = password
        self.elo = elo
        self.email = email
        self.pokemon_fan = pokemon_fan
        self.access_token = access_token

    def __str__(self):
        """Returns a string representation of the player.
        Returns:
            str: A string containing the username and Elo rating.
        """
        return f"Player({self.username}, elo: {self.elo})"

    def as_list(self) -> list[str]:
        """Returns the player's key attributes as a list.
        Returns:
            list[str]: A list containing [username, elo, email, pokemon_fan].
        """
        return [self.username, self.elo, self.email, self.pokemon_fan]