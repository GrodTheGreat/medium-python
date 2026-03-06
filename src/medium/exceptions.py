class NotFoundException(Exception):
    def __init__(self, message: str = "resource not found") -> None:
        super().__init__(message)
        self.message = message
