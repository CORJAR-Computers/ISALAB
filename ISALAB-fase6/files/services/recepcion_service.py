# services/recepcion_service.py
"""Lógica de negocio — Recepción de pacientes (ISAL-XXXX)"""

from datetime import datetime
from typing import List, Optional

from database.repositories import RecepcionRepository, AnimalRepository
from database.connection import DatabaseManager
from database.models import Recepcion
from utils.logger import setup_logger
from utils.security import Authorizer
from schemas.clinica import RecepcionSchema
from pydantic import ValidationError as PydanticValidationError
from utils.exceptions import BusinessLogicError, ValidationError
from config import ESTADOS_RECEPCION

logger = setup_logger()


class RecepcionService:
    """Servicio de recepción de pacientes.

    Fase 3 (issue C1 — RBAC bypass):
        - ``__init__`` acepta ``usuario_actual`` (opcional) y construye
          ``self.authorizer``. Si ``usuario_actual`` es ``None``, cae
          al thread-local ``get_current_user()`` (seteado por
          ``main.py`` tras el login).
        - Las operaciones de escritura (``registrar_recepcion``,
          ``actualizar_estado``) requieren rol ``asistente``.
        - Las operaciones de lectura (``obtener_recepcion``,
          ``listar_recepciones``, etc.) solo requieren usuario
          autenticado.

    Fase 3 (issue C2 — colisión ISAL-0001):
        - ``generar_codigo`` ahora usa ``DatabaseManager.generar_codigo(
          'ISAL')`` que hace el ``UPDATE contador SET ultimo = ultimo +
          1`` atómicamente. Antes, solo leía el contador sin
          incrementarlo, por lo que cada ``registrar_recepcion``
          producía ``ISAL-0001`` y chocaba con la UNIQUE constraint.
        - ``registrar_recepcion`` ya no llama a ``generar_codigo()``
          dos veces: si ``data['codigo']`` viene vacío, lo genera una
          vez (atómico) y lo conserva.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.repo = RecepcionRepository()
        self.animal_repo = AnimalRepository()
        self.db = DatabaseManager()
        self.authorizer = Authorizer(usuario_actual)

    # ── Código ────────────────────────────────────────────────────────────
    def generar_codigo(self) -> str:
        """Genera el siguiente código ISAL-XXXX atómicamente.

        Fase 3 (issue C2): antes era preview-only (no incrementaba),
        causando que cada ``registrar_recepcion`` chocara con la
        UNIQUE constraint en ``recepciones.codigo``. Ahora consume un
        número del contador de forma atómica, igual que los demás
        servicios (MuestraService.generar_codigo, etc.).
        """
        return self.db.generar_codigo('ISAL')

    # ── CRUD ──────────────────────────────────────────────────────────────
    def registrar_recepcion(self, data: dict):
        # RBAC: requiere rol asistente o superior
        self.authorizer.require_role('asistente')

        try:
            # Generar código automáticamente si no se proporciona.
            # Fase 3 (issue C2): el código se consume atómicamente aquí,
            # una sola vez. Antes, ``generar_codigo()`` era preview-only
            # y ``registrar_recepcion`` tampoco incrementaba → colisión.
            if not data.get('codigo'):
                data['codigo'] = self.generar_codigo()

            # 1. El guardia de seguridad revisa los datos
            datos_validados = RecepcionSchema(**data)

            # 2. Si pasa, lo convertimos a nuestro modelo tradicional y
            # guardamos
            recepcion = Recepcion(
                codigo=datos_validados.codigo,
                animal_id=datos_validados.animal_id,
                fecha_hora=datos_validados.fecha_hora,
                motivo=datos_validados.motivo,
                veterinario=datos_validados.veterinario,
                estado=datos_validados.estado,
                proxima_cita=datos_validados.proxima_cita,
                observaciones=datos_validados.observaciones
            )
            return self.repo.create(recepcion)

        except PydanticValidationError as e:
            # Formateamos el error para que la interfaz lo muestre bonito
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            raise BusinessLogicError(
                f"Datos inválidos en recepción:\n{error_msg}")

    def obtener_recepcion(self, rid: int) -> Recepcion:
        # RBAC: cualquier usuario autenticado puede consultar
        self.authorizer.require_authenticated()
        return self.repo.get_by_id(rid)

    def listar_recepciones(self, filtros: dict = None) -> List[Recepcion]:
        # RBAC: cualquier usuario autenticado puede listar
        self.authorizer.require_authenticated()
        return self.repo.get_all(filtros)

    def historial_paciente(self, animal_id: int) -> List[Recepcion]:
        # RBAC: cualquier usuario autenticado puede consultar
        self.authorizer.require_authenticated()
        return self.repo.get_by_animal(animal_id)

    def actualizar_estado(self, rid: int, estado: str,
                          proxima_cita: str = None) -> None:
        # RBAC: requiere rol asistente o superior
        self.authorizer.require_role('asistente')
        # Fase 5 (H-S4): validar ``estado`` contra whitelist
        # ``ESTADOS_RECEPCION``. Antes se aceptaba CUALQUIER string,
        # lo que permitía inyectar valores arbitrarios en la BD y
        # romper la UI (filtros, badges, colores) que asume un set
        # cerrado de estados.
        if estado not in ESTADOS_RECEPCION:
            raise ValidationError(
                f"Estado '{estado}' no válido. Estados permitidos: "
                f"{', '.join(ESTADOS_RECEPCION)}")
        self.repo.get_by_id(rid)   # valida existencia
        self.repo.update_estado(rid, estado, proxima_cita)
        logger.info(f"Recepción {rid} → estado: {estado}")

    def recepciones_hoy(self) -> List[Recepcion]:
        # RBAC: cualquier usuario autenticado puede consultar
        self.authorizer.require_authenticated()
        # Fase 6 (S-M6): antes se llamaba ``self.repo.get_all()`` (sin
        # filtros) y luego se filtraba en Python con ``r.fecha_hora.startswith(hoy)``,
        # trayendo TODAS las recepciones a memoria (potencialmente miles
        # de registros). Ahora delegamos el filtrado al motor SQL vía
        # rango ``fecha_hora >= :desde AND fecha_hora < :hasta`` en el
        # repositorio, que es ordenes de magnitud más eficiente y soporta
        # índices sobre la columna. Usamos ``fecha_desde``/``fecha_hasta``
        # en lugar de ``date(fecha_hora) = :hoy`` para permitir el uso
        # de un índice sobre la columna (``date(col)`` no usa índices en
        # SQLite).
        from datetime import datetime, timedelta
        hoy = datetime.now().date()
        desde = datetime.combine(hoy, datetime.min.time())
        hasta = desde + timedelta(days=1)
        return self.repo.get_all({
            'fecha_desde': desde.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_hasta': hasta.strftime('%Y-%m-%d %H:%M:%S'),
        })

    # Fase 6 (S-M2): eliminado ``_validar`` muerto. Era dead code —
    # ningún caller lo invocaba (``registrar_recepcion`` valida vía
    # ``RecepcionSchema`` de Pydantic). Replicaba reglas ya expresadas
    # en ``schemas/clinica.py::RecepcionSchema`` (animal_id > 0,
    # motivo min_length=1).
