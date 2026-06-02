from fastapi import status


class AppError(Exception):
    """Base class for all application-level errors."""

    default_message = "Something went wrong"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    default_message = "Resource not found"
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    default_message = "Conflict occurred"
    status_code = status.HTTP_409_CONFLICT


class ValidationError(AppError):
    default_message = "Validation failed"
    status_code = status.HTTP_400_BAD_REQUEST


class AuthenticationError(AppError):
    default_message = "Authentication failed"
    status_code = status.HTTP_401_UNAUTHORIZED


class PermissionDeniedError(AppError):
    default_message = "Permission denied"
    status_code = status.HTTP_403_FORBIDDEN


class ExternalServiceError(AppError):
    default_message = "External service error"
    status_code = status.HTTP_502_BAD_GATEWAY


class UserNotFoundError(NotFoundError):
    default_message = "User not found"


class UserAlreadyExistsError(ConflictError):
    default_message = "User already exists"


class InvalidCredentialsError(AuthenticationError):
    default_message = "Invalid credentials"


class UnauthorizedAccessError(PermissionDeniedError):
    default_message = "Unauthorized access"


class VerificationTokenNotFoundError(NotFoundError):
    default_message = "Invalid token"


class PostNotFoundError(NotFoundError):
    default_message = "Post not found"


class TooManyImagesError(ValidationError):
    default_message = "Image upload limit exceeded"


class CommentNotFoundError(NotFoundError):
    default_message = "Comment not found"


class FileValidationError(ValidationError):
    default_message = "Invalid file"


class UnsupportedFileTypeError(FileValidationError):
    default_message = "Unsupported file type"


class FileTooLargeError(FileValidationError):
    default_message = "File size exceeds limit"


class AlreadyFollowingError(ConflictError):
    default_message = "Already following this user"


class CannotFollowYourselfError(ValidationError):
    default_message = "You cannot follow yourself"


class FollowRequestNotFoundError(NotFoundError):
    default_message = "Follow request not found"
