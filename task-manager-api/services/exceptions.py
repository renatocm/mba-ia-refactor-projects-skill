"""Expected application failures, independent of HTTP."""
class ApplicationError(Exception):
    pass

class InvalidInput(ApplicationError):
    pass

class NotFound(ApplicationError):
    pass

class Conflict(ApplicationError):
    pass

class AccessDenied(ApplicationError):
    pass

class InvalidCredentials(ApplicationError):
    pass
