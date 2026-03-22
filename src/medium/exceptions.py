class MediumException(Exception):
    def __init__(self, message: str = "unexpected internal server error") -> None:
        super().__init__(message)
        self.message = message


class ValidationException(MediumException):
    pass
