# services/api-gateway/app/core/exceptions.py

class AppException(Exception):
    """应用自定义异常基类"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class GatewayTimeoutError(AppException):
    """网关超时异常"""
    def __init__(self, message: str = "Upstream service timeout"):
        super().__init__(message=message, status_code=504, error_code="GATEWAY_TIMEOUT")

class UpstreamServiceError(AppException):
    """上游服务错误"""
    def __init__(self, message: str = "Upstream service unavailable"):
        super().__init__(message=message, status_code=502, error_code="UPSTREAM_ERROR")