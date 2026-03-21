from medium.exceptions import MediumException


class EmailConflictException(MediumException):
    def __init__(self, message: str = "user with this email already exists") -> None:
        super().__init__(message)


class UsernameConflictException(MediumException):
    def __init__(self, message: str = "user with this username already exists") -> None:
        super().__init__(message)
