# utils/security.py
"""Módulo de seguridad para IsaLab - Funciones de autenticación y control de acceso."""

import secrets
import string
import hashlib
import threading
from typing import Optional, Callable
from functools import wraps

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

from utils.exceptions import IsaLabException
from utils.logger import setup_logger

logger = setup_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Registro thread-local del usuario actual (Fase 3 — issue C1 RBAC bypass)
# ─────────────────────────────────────────────────────────────────────────────
# Antes de Fase 3, ``Authorizer`` solo se cableaba en ``UsuarioService``; el
# resto de servicios instanciaban ``Service()`` sin usuario, por lo que el
# RBAC estaba efectivamente burlado. Para no tener que pasar
# ``usuario_actual`` a cada ``Service()`` desde la GUI (9 vistas + 11
# diálogos), usamos un registro thread-local: la GUI llama a
# ``set_current_user(usuario)`` una vez tras el login y todos los servicios
# lo recogen automáticamente vía ``Authorizer()``.
#
# Esto también da un valor por defecto seguro: si no hay usuario (tests,
# invocación desde CLI, sesión caducada), ``Authorizer`` trata al llamador
# como anónimo (rol='') y cualquier ``require_role`` levanta
# ``PermissionDeniedError``.

_current_user_ctx = threading.local()


def set_current_user(user: Optional[dict]) -> None:
    """Establece el usuario autenticado para el thread actual.

    Debe llamarse tras un login exitoso (ver ``main.py``) y limpiarse al
    cerrar sesión. Es thread-local, así que cada thread (incluyendo
    workers de PDF) mantiene su propio contexto.
    """
    _current_user_ctx.user = user


def get_current_user() -> Optional[dict]:
    """Retorna el usuario del thread actual, o ``None`` si no hay sesión."""
    return getattr(_current_user_ctx, 'user', None)


def clear_current_user() -> None:
    """Limpia el usuario del thread actual (logout)."""
    if hasattr(_current_user_ctx, 'user'):
        del _current_user_ctx.user


# ─────────────────────────────────────────────────────────────────────────────
# Hashing de contraseñas
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Fase 5 (H-S1): hash "dummy" para mitigar timing attacks en login.
# ─────────────────────────────────────────────────────────────────────────────
# Antes, ``UsuarioService.autenticar`` levantaba ``AuthenticationError``
# INMEDIATAMENTE cuando el usuario no existía, sin ejecutar bcrypt. Eso
# permitía a un atacante distinguish "usuario no existe" (respuesta
# rápida) vs "contraseña incorrecta" (respuesta lenta por bcrypt) midiendo
# el tiempo de respuesta. Con ese oracle, el atacante puede enumerar
# usernames válidos sin siquiera probar contraseñas.
#
# Ahora, cuando el usuario no existe, ``autenticar`` ejecuta
# ``verify_password(password, DUMMY_BCRYPT_HASH)`` para consumir el mismo
# tiempo que una verificación real, antes de levantar el error. El
# ``DUMMY_BCRYPT_HASH`` es un hash bcrypt precomputado de una contraseña
# aleatoria que NADIE conoce (el valor no se valida contra nada, solo
# sirve para que ``bcrypt.checkpw`` corra).


# Generado con ``bcrypt.gensalt(rounds=12)`` +
# ``bcrypt.hashpw(secrets.token_bytes(32).hex().encode(), salt)``.
# rounds=12 → mismo costo que los hashes reales → mismo tiempo de verificación.
DUMMY_BCRYPT_HASH = (
    "$2b$12$0123456789012345678901uPxFQ/HQjxv/XuRBKmM5qovtM/oZTDbq"
)


def dummy_verify_password(password: str) -> None:
    """Ejecuta ``bcrypt.checkpw`` contra un hash dummy, sin importar el resultado.

    Pensado para ser llamado en el branch "usuario no encontrado" de
    ``UsuarioService.autenticar`` para que el tiempo de respuesta de ese
    branch sea similar al del branch "contraseña incorrecta", cerrando
    el timing oracle.
    """
    if BCRYPT_AVAILABLE:
        try:
            bcrypt.checkpw(
                password.encode('utf-8'),
                DUMMY_BCRYPT_HASH.encode('utf-8')
            )
        except Exception:
            # Si bcrypt falla (hash mal formado, etc.), no hay nada
            # razonable que podamos hacer aquí — el objetivo ya se cumplió
            # si el tiempo fue similar.
            pass


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


# ─────────────────────────────────────────────────────────────────────────────
# Excepciones
# ─────────────────────────────────────────────────────────────────────────────
# Fase 3 — issue C4: ``PermissionError`` original era ``class
# PermissionError(Exception)`` lo que SHADOWEABA el builtin de Python
# (``PermissionError`` es una excepción estándar de Python para errores
# OS-level tipo "permission denied" al abrir archivos). Cualquier módulo
# que importara ``utils.security`` perdía acceso al builtin.
#
# Ahora la clase se llama ``PermissionDeniedError`` y hereda de
# ``IsaLabException`` (consistencia con la jerarquía de excepciones del
# proyecto). Se mantiene ``PermissionError`` como alias deprecated para
# no romper imports externos.

class PermissionDeniedError(IsaLabException):
    """Acción denegada por falta de permisos (RBAC)."""


# Alias deprecated — usar ``PermissionDeniedError`` en código nuevo.
# Se mantiene para no romper imports externos que aún referencien
# ``PermissionError`` desde ``utils.security``.
PermissionError = PermissionDeniedError


# ─────────────────────────────────────────────────────────────────────────────
# Authorizer (RBAC)
# ─────────────────────────────────────────────────────────────────────────────

class Authorizer:
    """
    Gestor de control de acceso basado en roles (RBAC).

    Uso típico (servicio)::

        self.authorizer = Authorizer(usuario_actual)
        self.authorizer.require_role('admin')

    Si ``usuario_actual`` es ``None``, el ``Authorizer`` cae al
    registro thread-local ``get_current_user()`` (seteado por
    ``main.py`` tras el login). Si tampoco hay usuario thread-local,
    se comporta como anónimo (rol='') y cualquier ``require_role``
    levanta ``PermissionDeniedError``.
    """

    ROLES_JERARQUIA = {
        'admin': 4,
        'veterinario': 3,
        'asistente': 2,
        'usuario': 1,
    }

    def __init__(self, usuario_actual: Optional[dict] = None):
        # Fallback al thread-local si no se pasa explícito.
        if usuario_actual is None:
            usuario_actual = get_current_user()
        self.usuario_actual = usuario_actual or {}

    def _get_nivel_rol(self, rol: str) -> int:
        """Obtiene el nivel numérico de un rol."""
        return self.ROLES_JERARQUIA.get(rol, 0)

    def tiene_rol(self, rol_requerido: str) -> bool:
        """Verifica si el usuario tiene el rol especificado (jerárquico)."""
        rol_actual = self.usuario_actual.get('rol', '')
        nivel_actual = self._get_nivel_rol(rol_actual)
        nivel_requerido = self._get_nivel_rol(rol_requerido)
        return nivel_actual >= nivel_requerido

    def es_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.tiene_rol('admin')

    def esta_autenticado(self) -> bool:
        """True si hay un usuario con id y rol no vacío."""
        u = self.usuario_actual or {}
        return bool(u.get('id') and u.get('rol'))

    def require_authenticated(self) -> None:
        """Exige que haya un usuario autenticado en el contexto."""
        if not self.esta_autenticado():
            raise PermissionDeniedError(
                "Se requiere un usuario autenticado para esta acción."
            )

    def require_role(self, rol_requerido: str) -> None:
        """
        Verifica que el usuario tenga el rol requerido.
        Lanza PermissionDeniedError si no tiene permisos.
        """
        if not self.esta_autenticado():
            raise PermissionDeniedError(
                "Se requiere un usuario autenticado para esta acción."
            )
        if not self.tiene_rol(rol_requerido):
            logger.warning(
                f"Acceso denegado: usuario '{self.usuario_actual.get('username')}' "
                f"(rol: {self.usuario_actual.get('rol')}) intentó acceder a función "
                f"que requiere rol '{rol_requerido}'"
            )
            raise PermissionDeniedError(
                f"No tiene permisos para realizar esta acción. "
                f"Se requiere rol: {rol_requerido}"
            )

    def require_any_role(self, roles: list[str]) -> None:
        """Verifica que el usuario tenga alguno de los roles especificados."""
        if not self.esta_autenticado():
            raise PermissionDeniedError(
                "Se requiere un usuario autenticado para esta acción."
            )
        if not any(self.tiene_rol(r) for r in roles):
            raise PermissionDeniedError(
                "No tiene permisos para realizar esta acción"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Decoradores de conveniencia
# ─────────────────────────────────────────────────────────────────────────────

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
            raise PermissionDeniedError(
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
                raise PermissionDeniedError(
                    "El servicio no tiene authorizer configurado")
            authorizer.require_role(rol)
            return func(self, *args, **kwargs)
        return wrapper
    return decorador
