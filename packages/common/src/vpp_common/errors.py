from enum import IntEnum


class ErrorCode(IntEnum):
    INVALID_REQUEST = 40001
    MISSING_REQUIRED_FIELD = 40002
    INVALID_TIMESTAMP = 40003
    INVALID_ENUM_VALUE = 40004
    PAYLOAD_TOO_LARGE = 40005

    MISSING_IDENTITY = 40101
    INVALID_DID = 40102
    INVALID_SIGNATURE = 40103
    INVALID_HASH = 40104

    ACCESS_DENIED = 40301
    AUTHORIZATION_REQUIRED = 40302
    AUTHORIZATION_EXPIRED = 40303

    RESOURCE_NOT_FOUND = 40401
    BUSINESS_NOT_FOUND = 40402
    TRAINING_TASK_NOT_FOUND = 40403
    MODEL_VERSION_NOT_FOUND = 40404

    IDEMPOTENCY_CONFLICT = 40901
    INVALID_RESOURCE_STATE = 40902
    DUPLICATE_EVENT = 40903

    PARTICIPANTS_NOT_READY = 42201
    INSUFFICIENT_UPDATES = 42202
    UNSUPPORTED_PRIVACY_MODE = 42203
    INVALID_TRAINING_CONFIGURATION = 42204

    RATE_LIMIT_EXCEEDED = 42901

    INTERNAL_ERROR = 50001
    STORAGE_ERROR = 50002
    SERIALIZATION_ERROR = 50003

    DOWNSTREAM_REJECTED = 50201
    DOWNSTREAM_INVALID_RESPONSE = 50202
    DOWNSTREAM_UNAVAILABLE = 50203

    SERVICE_UNAVAILABLE = 50301
    DEPENDENCY_UNAVAILABLE = 50302
    MAINTENANCE_MODE = 50303

    DOWNSTREAM_TIMEOUT = 50401


ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_REQUEST: "invalid request",
    ErrorCode.MISSING_REQUIRED_FIELD: "missing required field",
    ErrorCode.INVALID_TIMESTAMP: "invalid timestamp",
    ErrorCode.INVALID_ENUM_VALUE: "invalid enum value",
    ErrorCode.PAYLOAD_TOO_LARGE: "payload too large",
    ErrorCode.MISSING_IDENTITY: "missing identity",
    ErrorCode.INVALID_DID: "invalid did",
    ErrorCode.INVALID_SIGNATURE: "invalid signature",
    ErrorCode.INVALID_HASH: "invalid hash",
    ErrorCode.ACCESS_DENIED: "access denied",
    ErrorCode.AUTHORIZATION_REQUIRED: "authorization required",
    ErrorCode.AUTHORIZATION_EXPIRED: "authorization expired",
    ErrorCode.RESOURCE_NOT_FOUND: "resource not found",
    ErrorCode.BUSINESS_NOT_FOUND: "business not found",
    ErrorCode.TRAINING_TASK_NOT_FOUND: "training task not found",
    ErrorCode.MODEL_VERSION_NOT_FOUND: "model version not found",
    ErrorCode.IDEMPOTENCY_CONFLICT: "idempotency conflict",
    ErrorCode.INVALID_RESOURCE_STATE: "invalid resource state",
    ErrorCode.DUPLICATE_EVENT: "duplicate event",
    ErrorCode.PARTICIPANTS_NOT_READY: "participants not ready",
    ErrorCode.INSUFFICIENT_UPDATES: "insufficient updates",
    ErrorCode.UNSUPPORTED_PRIVACY_MODE: "unsupported privacy mode",
    ErrorCode.INVALID_TRAINING_CONFIGURATION: "invalid training configuration",
    ErrorCode.RATE_LIMIT_EXCEEDED: "rate limit exceeded",
    ErrorCode.INTERNAL_ERROR: "internal error",
    ErrorCode.STORAGE_ERROR: "storage error",
    ErrorCode.SERIALIZATION_ERROR: "serialization error",
    ErrorCode.DOWNSTREAM_REJECTED: "downstream rejected",
    ErrorCode.DOWNSTREAM_INVALID_RESPONSE: "downstream invalid response",
    ErrorCode.DOWNSTREAM_UNAVAILABLE: "downstream unavailable",
    ErrorCode.SERVICE_UNAVAILABLE: "service unavailable",
    ErrorCode.DEPENDENCY_UNAVAILABLE: "dependency unavailable",
    ErrorCode.MAINTENANCE_MODE: "maintenance mode",
    ErrorCode.DOWNSTREAM_TIMEOUT: "downstream timeout",
}


def http_status_for(code: ErrorCode | int) -> int:
    error_code = ErrorCode(code)
    status = int(error_code) // 100
    return status if status in {400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504} else 500
