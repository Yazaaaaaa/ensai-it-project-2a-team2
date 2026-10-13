from business_object.user import User


class Admin(User):
    """Business object representing a user with an admin role"""

    def __init__(self, id: int, email: str, password_hash: str, role: str, created_at: datetime):
        super().__init__(id)
        super().__init__(email)
        super().__init__(password_hash)
        super().__init__(role)
        super().__init__(created_at)

  
