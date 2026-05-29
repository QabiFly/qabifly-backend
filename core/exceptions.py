from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotAuthenticated
from rest_framework import status
from .responses import error_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            return error_response(
                message="Validation error",
                errors=response.data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            return error_response(
                message="Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            return error_response(
                message=str(exc.detail) if hasattr(exc, "detail") else "Server error",
                status_code=response.status_code,
            )

    return error_response(
        message="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )