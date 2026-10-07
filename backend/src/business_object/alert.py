class Alert:
    """Business object that represents an alert"""

    def __init__(self, id, user_id, neo_id):
        self.id = id
        self.user_id = user_id
        self.neo_id = neo_id
