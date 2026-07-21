# utils/security.py
"""Módulo de seguridad para IsaLab - Funciones de autenticación y control de acceso"""

import secrets
import string
import hashlib
from typing import Optional, Callable
from functools import wraps

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

from utils.logger import setup_logger

logger = setup_logger()


def _generar_salt() -> str:
    """Genera un salt aleatorio seguro."""
    return secrets.token_hex(16)


def hash_password(password: str) -> str:
    """
    Genera un hash seguro de la contraseña usando bcrypt.
    Si bcrypt no está disponible, usa PBKDF2 como fallback.
    Incluye salt único por usuario.
    """
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    else:
        salt = _generar_salt()
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica una contraseña contra su hash.
    Compatible con bcrypt, PBKDF2 y SHA256 legacy (para migración).
    """
    if BCRYPT_AVAILABLE and password_hash.startswith('$2'):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    elif '$' in password_hash:
        salt, stored_hash = password_hash.split('$', 1)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(pwd_hash.hex(), stored_hash)
    elif len(password_hash) == 64:
        computed = hashlib.sha256(password.encode()).hexdigest()
        return secrets.compare_digest(computed, password_hash)
    else:
        return False


def necesita_migracion(password_hash: str) -> bool:
    """Verifica si el hash necesita migrarse a bcrypt."""
    if not BCRYPT_AVAILABLE:
        return False
    return not password_hash.startswith('$2')


def hash_legacy_sha256(password: str) -> str:
    """Genera hash SHA256 legacy (para compatibilidad)."""
    return hashlib.sha256(password.encode()).hexdigest()


def generar_password_temporal(longitud: int = 12) -> str:
    """
    Genera una contraseña temporal segura.
    Incluye letras, números y símbolos.
    """
    if longitud < 4:
        raise ValueError(
            "La longitud mínima para una contraseña temporal es 4")

    caracteres = (
        string.ascii_uppercase +
        string.ascii_lowercase +
        string.digits +
        string.punctuation
    )
    while True:
        password = ''.join(secrets.choice(caracteres) for _ in range(longitud))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            return password


def validar_fortaleza_password(password: str) -> tuple[bool, str]:
    """
    Valida la fortaleza de una contraseña.
    Retorna (es_valida, mensaje_error).
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if len(password) > 128:
        return False, "La contraseña no puede exceder 128 caracteres"
    if not any(c.isupper() for c in password):
        return False, "Debe incluir al menos una letra mayúscula"
    if not any(c.islower() for c in password):
        return False, "Debe incluir al menos una letra minúscula"
    if not any(c.isdigit() for c in password):
        return False, "Debe incluir al menos un número"
    return True, ""


class AuthorizationError(Exception):
    """Excepción para errores de permisos."""


class Authorizer:
    """
    Gestor de control de acceso basado en roles (RBAC).
    Uso:
        auth = Authorizer(usuario_actual)
        auth.require_role('admin')
    """

    ROLES_JERARQUIA = {
        'admin': 4,
        'veterinario': 3,
        'asistente': 2,
        'usuario': 1,
    }

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.usuario_actual = usuario_actual or {}

    def _get_nivel_rol(self, rol: str) -> int:
        """Obtiene el nivel numérico de un rol."""
        return self.ROLES_JERARQUIA.get(rol, 0)

    def tiene_rol(self, rol_requerido: str) -> bool:
        """Verifica si el usuario tiene el rol especificado."""
        rol_actual = self.usuario_actual.get('rol', '')
        nivel_actual = self._get_nivel_rol(rol_actual)
        nivel_requerido = self._get_nivel_rol(rol_requerido)
        return nivel_actual >= nivel_requerido

    def es_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.tiene_rol('admin')

    def require_role(self, rol_requerido: str) -> None:
        """
        Verifica que el usuario tenga el rol requerido.
        Lanza PermissionError si no tiene permisos.
        """
        if not self.tiene_rol(rol_requerido):
            logger.warning(
                f"Acceso denegado: usuario '{self.usuario_actual.get('username')}' "
                f"(rol: {self.usuario_actual.get('rol')}) intentó acceder a función "
                f"que requiere rol '{rol_requerido}'"
            )
            raise PermissionError(
                f"No tiene permisos para realizar esta acción. "
                f"Se requiere rol: {rol_requerido}"
            )

    def require_any_role(self, roles: list[str]) -> None:
        """Verifica que el usuario tenga alguno de los roles especificados."""
        if not any(self.tiene_rol(r) for r in roles):
            raise PermissionError(
                "No tiene permisos para realizar esta acción"
            )


def decorador_requerir_admin(func: Callable) -> Callable:
    """
    Decorador para requerir rol admin en un método.
    Uso:
        @decorador_requerir_admin
        def metodo_sensible(self, ...):
            ...
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        authorizer = getattr(self, 'authorizer', None)
        if authorizer is None:
            raise PermissionError(
                "El servicio no tiene authorizer configurado")
        authorizer.require_role('admin')
        return func(self, *args, **kwargs)
    return wrapper


def decorador_requerir_rol(rol: str) -> Callable:
    """Decorador genérico para requerir un rol específico."""
    def decorador(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            authorizer = getattr(self, 'authorizer', None)
            if authorizer is None:
                raise PermissionError(
                    "El servicio no tiene authorizer configurado")
            authorizer.require_role(rol)
            return func(self, *args, **kwargs)
        return wrapper
    return decorador


# Alias de compatibilidad
PermissionError = AuthorizationError
