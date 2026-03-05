class JyError(Exception):
    """Base error for JianYing skill scripts."""


class UserInputError(JyError):
    """Invalid user input/arguments."""


class InfraError(JyError):
    """Infrastructure/runtime dependency failures."""


class DataError(JyError):
    """Data format or content invalid."""
