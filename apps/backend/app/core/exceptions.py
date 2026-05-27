"""
Excepciones personalizadas de la aplicación.
"""
from typing import Any, Optional


class BaseAppException(Exception):
    """Excepción base de la aplicación."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "APP_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(self.message)


# Alias para compatibilidad
AppException = BaseAppException


class NotFoundException(BaseAppException):
    """Recurso no encontrado."""
    
    def __init__(self, message: str = "Recurso no encontrado", details: Optional[Any] = None):
        super().__init__(message, 404, "NOT_FOUND", details)


class UnauthorizedException(BaseAppException):
    """No autorizado."""
    
    def __init__(self, message: str = "No autorizado", details: Optional[Any] = None):
        super().__init__(message, 401, "UNAUTHORIZED", details)


# Alias para errores de autenticación
AuthenticationException = UnauthorizedException


class ForbiddenException(BaseAppException):
    """Acceso prohibido."""
    
    def __init__(self, message: str = "Acceso prohibido", details: Optional[Any] = None):
        super().__init__(message, 403, "FORBIDDEN", details)


class BadRequestException(BaseAppException):
    """Solicitud incorrecta."""
    
    def __init__(self, message: str = "Solicitud incorrecta", details: Optional[Any] = None):
        super().__init__(message, 400, "BAD_REQUEST", details)


class ValidationException(BaseAppException):
    """Error de validación."""
    
    def __init__(self, message: str = "Error de validación", details: Optional[Any] = None):
        super().__init__(message, 422, "VALIDATION_ERROR", details)


class BusinessRuleException(BaseAppException):
    """Violación de regla de negocio."""
    
    def __init__(self, message: str = "Regla de negocio violada", details: Optional[Any] = None):
        super().__init__(message, 422, "BUSINESS_RULE_ERROR", details)


class DuplicateException(BaseAppException):
    """Recurso duplicado."""
    
    def __init__(self, message: str = "Recurso duplicado", details: Optional[Any] = None):
        super().__init__(message, 409, "DUPLICATE_ERROR", details)


# Alias para conflictos
ConflictException = DuplicateException


class InvalidStateException(BaseAppException):
    """Estado inválido para la operación."""
    
    def __init__(self, message: str = "Estado inválido", details: Optional[Any] = None):
        super().__init__(message, 400, "INVALID_STATE", details)


class ExternalServiceException(BaseAppException):
    """Error en servicio externo."""
    
    def __init__(self, message: str = "Error en servicio externo", details: Optional[Any] = None):
        super().__init__(message, 503, "EXTERNAL_SERVICE_ERROR", details)


class FileException(BaseAppException):
    """Error relacionado con archivos."""
    
    def __init__(self, message: str = "Error de archivo", details: Optional[Any] = None):
        super().__init__(message, 400, "FILE_ERROR", details)


class StorageException(BaseAppException):
    """Error en el sistema de almacenamiento."""
    
    def __init__(self, message: str = "Error de almacenamiento", details: Optional[Any] = None):
        super().__init__(message, 500, "STORAGE_ERROR", details)

