from business_object.user import User


class ClassicMember(User):
    """Business object representing a user with an classic member role (a user with no admin role)"""

    def __init__(self, id: int, email: str, password_hash: str, role: str, created_at: datetime):
        super().__init__(id)
        super().__init__(email)
        super().__init__(password_hash)
        super().__init__(role)
        super().__init__(created_at)
