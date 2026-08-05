from .codes import ErrorCode


class GatewayException(Exception):

    def __init__(
        self,
        message: str,
        code: int = ErrorCode.INTERNAL_ERROR,
    ):

        self.message = message
        self.code = code

        super().__init__(message)