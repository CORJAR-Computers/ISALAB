# utils/exceptions.py
"""Excepciones personalizadas de IsaLab"""


class IsaLabException(Exception):
    """Excepción base"""

    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class DatabaseError(IsaLabException):
    """Errores de base de datos"""


class ValidationError(IsaLabException):
    """Errores de validación"""


class BusinessLogicError(IsaLabException):
    """Errores de lógica de negocio"""


class NotFoundError(IsaLabException):
    """Recurso no encontrado"""


class DuplicateError(IsaLabException):
    """Registro duplicado"""


class AuthenticationError(IsaLabException):
    """Error de autenticación (usuario o contraseña incorrectos)"""


class AuthorizationError(IsaLabException):
    """Error de autorizacion (sin permisos suficientes)"""
