# services/usuario_service.py
"""Servicio de usuarios para autenticación con seguridad mejorada"""

from typing import Optional
from database.connection import DatabaseManager
from utils.exceptions import AuthenticationError, NotFoundError, DuplicateError
from utils.logger import setup_logger
from utils.security import (
    hash_password,
    verify_password,
    validar_fortaleza_password,
    Authorizer,
    PermissionDeniedError,
    generar_password_temporal,
    necesita_migracion,
)

logger = setup_logger()

CAMPOS_PERMITIDOS_ACTUALIZAR = {'nombre', 'rol'}


class UsuarioService:
    def __init__(self, usuario_actual: Optional[dict] = None):
        self.db = DatabaseManager()
        self.authorizer = Authorizer(usuario_actual)

    def _verificar_admin(self) -> None:
        """Verifica que el usuario actual tenga permisos de admin."""
        self.authorizer.require_role('admin')

    def autenticar(self, username: str, password: str) -> dict:
        """
        Autentica un usuario y retorna sus datos.
        Implementa protección contra timing attacks.
        """
        username_normalized = username.strip().lower()
        logger.info(f"Intentando autenticar usuario: {username_normalized}")

        query = "SELECT id, username, nombre, rol, password_hash FROM usuarios WHERE username = ? AND activo = 1"
        row = self.db.fetch_one(query, (username_normalized,))

        if not row:
            logger.warning(
                f"Login fallido: usuario no encontrado: {username_normalized}")
            raise AuthenticationError("Usuario o contraseña incorrectos")

        if not verify_password(password, row['password_hash']):
            logger.warning(
                f"Login fallido: contraseña incorrecta para: {username_normalized}")
            raise AuthenticationError("Usuario o contraseña incorrectos")

        logger.info(
            f"Usuario autenticado exitosamente: {username_normalized}, rol: {
                row['rol']}")

        if necesita_migracion(row['password_hash']):
            nuevo_hash = hash_password(password)
            self.db.execute(
                "UPDATE usuarios SET password_hash = ? WHERE id = ?",
                (nuevo_hash, row['id'])
            )
            logger.info(
                f"Hash migrado a bcrypt para usuario: {username_normalized}")

        self.db.execute(
            "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = ?",
            (row['id'],)
        )

        return {
            'id': row['id'],
            'username': row['username'],
            'nombre': row['nombre'],
            'rol': row['rol']
        }

    def cambiar_password(
            self,
            usuario_id: int,
            password_actual: str,
            password_nueva: str) -> bool:
        """Cambia la contraseña de un usuario."""
        es_valida, mensaje = validar_fortaleza_password(password_nueva)
        if not es_valida:
            raise AuthenticationError(mensaje)

        query = "SELECT id, password_hash FROM usuarios WHERE id = ? AND activo = 1"
        row = self.db.fetch_one(query, (usuario_id,))

        if not row or not verify_password(
                password_actual, row['password_hash']):
            raise AuthenticationError("La contraseña actual no es correcta")

        nuevo_hash = hash_password(password_nueva)
        self.db.execute(
            "UPDATE usuarios SET password_hash = ? WHERE id = ?",
            (nuevo_hash, usuario_id)
        )
        logger.info(f"Contraseña actualizada para usuario ID: {usuario_id}")
        return True

    def crear_usuario(
            self,
            username: str,
            password: str,
            nombre: str,
            rol: str = "usuario"
    ) -> int:
        """
        Crea un nuevo usuario.
        Requiere permisos de administrador.
        """
        self._verificar_admin()

        username_normalized = username.strip().lower()

        if len(username_normalized) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")

        es_valida, mensaje = validar_fortaleza_password(password)
        if not es_valida:
            raise ValueError(mensaje)

        if rol not in ('admin', 'veterinario', 'asistente', 'usuario'):
            raise ValueError(f"Rol '{rol}' no válido")

        existe = self.db.fetch_one(
            "SELECT id FROM usuarios WHERE username = ?",
            (username_normalized,)
        )
        if existe:
            raise DuplicateError(
                f"Ya existe un usuario con el username '{username_normalized}'")

        password_hash = hash_password(password)
        query = "INSERT INTO usuarios (username, password_hash, nombre, rol) VALUES (?, ?, ?, ?)"
        cursor = self.db.execute(
            query, (username_normalized, password_hash, nombre, rol))
        logger.info(f"Usuario creado: {username_normalized} con rol {rol}")
        return cursor.lastrowid

    def crear_usuario_inicial(
            self,
            username: str,
            password: str,
            nombre: str
    ) -> int:
        """
        Crea el primer usuario administrador.
        Solo funciona si NO existe ningún usuario en el sistema.
        """
        row = self.db.fetch_one("SELECT COUNT(*) as total FROM usuarios")
        if row and row['total'] > 0:
            raise PermissionDeniedError(
                "Ya existen usuarios en el sistema. Use crear_usuario() con permisos de admin."
            )

        username_normalized = username.strip().lower()

        if len(username_normalized) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")

        es_valida, mensaje = validar_fortaleza_password(password)
        if not es_valida:
            raise ValueError(
                f"La contraseña no es segura: {mensaje}. "
                "Use al menos 8 caracteres, incluyendo mayúsculas, minúsculas, números y símbolos."
            )

        password_hash = hash_password(password)
        query = "INSERT INTO usuarios (username, password_hash, nombre, rol) VALUES (?, ?, ?, ?)"
        cursor = self.db.execute(
            query, (username_normalized, password_hash, nombre, 'admin'))
        logger.info(
            f"Usuario administrador inicial creado: {username_normalized}")
        return cursor.lastrowid

    def listar_usuarios(self, solo_activos: bool = True) -> list:
        """Lista todos los usuarios."""
        self._verificar_admin()

        query = "SELECT id, username, nombre, rol, activo, created_at FROM usuarios"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY id"
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows]

    def obtener_usuario(self, usuario_id: int) -> dict:
        """Obtiene un usuario por ID."""
        self._verificar_admin()

        row = self.db.fetch_one(
            "SELECT id, username, nombre, rol, activo FROM usuarios WHERE id = ?",
            (usuario_id,)
        )
        if not row:
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")
        return dict(row)

    def actualizar_usuario(self, usuario_id: int, data: dict) -> None:
        """
        Actualiza datos de un usuario (excepto contraseña).
        Usa lista blanca de campos permitidos.
        """
        self._verificar_admin()

        campos_actualizar = []
        valores = []

        for campo, valor in data.items():
            if campo in CAMPOS_PERMITIDOS_ACTUALIZAR:
                if campo == 'rol' and valor not in (
                        'admin', 'veterinario', 'asistente', 'usuario'):
                    raise ValueError(f"Rol '{valor}' no válido")
                campos_actualizar.append(f"{campo} = ?")
                valores.append(valor)

        if not campos_actualizar:
            return

        valores.append(usuario_id)
        query = f"UPDATE usuarios SET {
            ', '.join(campos_actualizar)} WHERE id = ?"
        self.db.execute(query, tuple(valores))
        logger.info(
            f"Usuario {usuario_id} actualizado: {
                ', '.join(campos_actualizar)}")

    def desactivar_usuario(self, usuario_id: int) -> None:
        """Desactiva un usuario (eliminación lógica)."""
        self._verificar_admin()

        row = self.db.fetch_one(
            "SELECT rol FROM usuarios WHERE id = ?", (usuario_id,))
        if row and row['rol'] == 'admin':
            total_admins = self.db.fetch_one(
                "SELECT COUNT(*) as total FROM usuarios WHERE rol = 'admin' AND activo = 1"
            )
            if total_admins and total_admins['total'] <= 1:
                raise PermissionDeniedError(
                    "No se puede desactivar el último administrador")

        self.db.execute(
            "UPDATE usuarios SET activo = 0 WHERE id = ?", (usuario_id,))
        logger.info(f"Usuario {usuario_id} desactivado")

    def activar_usuario(self, usuario_id: int) -> None:
        """Reactivar un usuario."""
        self._verificar_admin()
        self.db.execute(
            "UPDATE usuarios SET activo = 1 WHERE id = ?", (usuario_id,))
        logger.info(f"Usuario {usuario_id} reactivado")

    def cambiar_password_admin(
            self,
            usuario_id: int,
            nueva_password: str) -> None:
        """Cambia la contraseña de un usuario (solo admin)."""
        self._verificar_admin()

        es_valida, mensaje = validar_fortaleza_password(nueva_password)
        if not es_valida:
            raise ValueError(mensaje)

        pwd_hash = hash_password(nueva_password)
        self.db.execute(
            "UPDATE usuarios SET password_hash = ? WHERE id = ?",
            (pwd_hash,
             usuario_id))
        logger.info(f"Contraseña actualizada para usuario ID: {usuario_id}")

    def reset_password(self, usuario_id: int) -> str:
        """
        Genera una nueva contraseña temporal para un usuario.
        Requiere permisos de admin.
        Retorna la nueva contraseña temporal.
        """
        self._verificar_admin()

        nueva_password = generar_password_temporal()
        pwd_hash = hash_password(nueva_password)
        self.db.execute(
            "UPDATE usuarios SET password_hash = ? WHERE id = ?",
            (pwd_hash, usuario_id)
        )
        logger.info(f"Contraseña reseteada para usuario ID: {usuario_id}")
        return nueva_password
