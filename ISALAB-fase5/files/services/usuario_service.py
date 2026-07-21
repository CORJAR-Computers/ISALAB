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
    dummy_verify_password,
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

        Fase 5 (H-S1): antes, cuando el username no existía, se
        levantaba ``AuthenticationError`` inmediatamente sin ejecutar
        bcrypt. Eso permitía a un atacante distinguir "usuario no
        existe" (respuesta rápida) vs "contraseña incorrecta" (lenta)
        midiendo tiempos de respuesta, convirtiendo el login en un
        oracle de enumeración de usernames. Ahora, en el branch
        "no encontrado", ejecutamos ``dummy_verify_password(password)``
        para consumir el mismo tiempo que una verificación real antes
        de levantar el error.

        Fase 5 (H-S6): el dict de retorno ahora incluye
        ``'password_reset_required': bool`` — la GUI puede consultarlo
        para forzar el cambio de contraseña tras un ``reset_password``
        del admin. Antes, la contraseña temporal era permanente.
        """
        username_normalized = username.strip().lower()
        logger.info(f"Intentando autenticar usuario: {username_normalized}")

        # Fase 5 (H-S6): seleccionamos también la flag
        # ``password_reset_required`` (añadida por la migración
        # ``c1a2b3c4d5e6``). Usamos ``COALESCE`` para tolerar BDs
        # antiguas donde la columna todavía no exista.
        query = (
            "SELECT id, username, nombre, rol, password_hash, "
            "COALESCE(password_reset_required, 0) AS password_reset_required "
            "FROM usuarios WHERE username = ? AND activo = 1"
        )
        row = self.db.fetch_one(query, (username_normalized,))

        if not row:
            # Fase 5 (H-S1): ejecutar bcrypt contra un hash dummy para
            # que el tiempo de respuesta sea similar al branch
            # "contraseña incorrecta" y cerrar el timing oracle.
            dummy_verify_password(password)
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
            'rol': row['rol'],
            # Fase 5 (H-S6): flag para forzar cambio de contraseña
            # en el próximo login si fue reseteada por admin.
            'password_reset_required': bool(row['password_reset_required']),
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
        # Fase 5 (H-S6): limpiar la flag ``password_reset_required``
        # porque el usuario acaba de setear una contraseña nueva. Antes,
        # la flag (seteada por ``reset_password``) quedaba en 1 para
        # siempre porque nadie la limpiaba.
        self.db.execute(
            "UPDATE usuarios SET password_hash = ?, password_reset_required = 0 "
            "WHERE id = ?",
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
        # Fase 5 (H-S6): limpiar la flag — el admin seteó la contraseña
        # manualmente, no es una temporal.
        self.db.execute(
            "UPDATE usuarios SET password_hash = ?, password_reset_required = 0 "
            "WHERE id = ?",
            (pwd_hash,
             usuario_id))
        logger.info(f"Contraseña actualizada para usuario ID: {usuario_id}")

    def reset_password(self, usuario_id: int) -> str:
        """
        Genera una nueva contraseña temporal para un usuario.
        Requiere permisos de admin.
        Retorna la nueva contraseña temporal.

        Fase 5 (H-S6): setea ``password_reset_required = 1`` para que
        la GUI de login pueda forzar al usuario a cambiarla en su
        próximo inicio de sesión. Antes, la contraseña temporal era
        permanente — un riesgo si el canal de entrega era interceptado.
        """
        self._verificar_admin()

        nueva_password = generar_password_temporal()
        pwd_hash = hash_password(nueva_password)
        # Fase 5 (H-S6): setear la flag de "cambio forzado".
        self.db.execute(
            "UPDATE usuarios SET password_hash = ?, password_reset_required = 1 "
            "WHERE id = ?",
            (pwd_hash, usuario_id)
        )
        logger.info(f"Contraseña reseteada para usuario ID: {usuario_id}")
        return nueva_password

    def requires_password_change(self, usuario_id: int) -> bool:
        """Indica si el usuario debe cambiar su contraseña en el próximo login.

        Fase 5 (H-S6): helper para que la GUI de login consulte la flag
        sin tener que re-ejecutar la query de autenticación. Usa
        ``COALESCE`` para tolerar BDs donde la columna no exista todavía.
        """
        row = self.db.fetch_one(
            "SELECT COALESCE(password_reset_required, 0) AS flag "
            "FROM usuarios WHERE id = ?",
            (usuario_id,)
        )
        return bool(row['flag']) if row else False
