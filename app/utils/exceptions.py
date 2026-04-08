class AppError(Exception):
    pass


class ValidationError(AppError):
    pass


class AuthenticationError(AppError):
    pass


class DuplicateVoteError(AppError):
    pass


class ElectionStateError(AppError):
    pass

