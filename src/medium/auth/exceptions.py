from medium.exceptions import MediumException


class PasswordMismatchException(MediumException):
    def __init__(self, message: str = "passwords don't match") -> None:
        super().__init__(message)


class InvalidCredentialsException(MediumException):
    def __init__(self, message: str = "invalid credentials") -> None:
        super().__init__(message)
