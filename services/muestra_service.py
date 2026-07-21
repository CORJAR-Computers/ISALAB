# services/muestra_service.py
"""Lógica de negocio para muestras"""

from typing import List, Dict, Optional, Any
from database.repositories import MuestraRepository, AnimalRepository
from database.connection import DatabaseManager
from database.models import Muestra
from utils.validators import MuestraValidator
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


class MuestraService:
    """Servicio de muestras de laboratorio.

    Fase 3 (issue C1 — RBAC bypass):
        - ``registrar_muestra`` requiere rol ``asistente`` o superior.
        - ``actualizar_estado`` requiere rol ``veterinario`` (es una
          acción clínica: cambiar estado / cargar resultados).
        - Lectura (``obtener_muestra``, ``listar_muestras``,
          ``obtener_pendientes``, ``obtener_urgentes``) solo requiere
          usuario autenticado.
        - ``generar_codigo`` consume el contador atómico (igual que
          antes) — no requiere rol especial pero sí autenticación.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.muestra_repo = MuestraRepository()
        self.animal_repo = AnimalRepository()
        self.db_manager = DatabaseManager()
        self.authorizer = Authorizer(usuario_actual)

    def obtener_muestra(self, muestra_id: int) -> Muestra:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.muestra_repo.get_by_id(muestra_id)

    def registrar_muestra(self, data: Dict[str, Any]) -> Muestra:
        # RBAC: requiere rol asistente o superior
        self.authorizer.require_role('asistente')

        try:
            MuestraValidator.validate(data)
            # Verifica que el paciente exista
            self.animal_repo.get_by_id(data['animal_id'])

            # Generar código automáticamente si no se proporciona
            codigo = data.get('codigo')
            if not codigo:
                codigo = self.generar_codigo()

            muestra = Muestra(
                codigo=codigo,
                animal_id=data['animal_id'],
                empresa=data.get('empresa'),  # <-- CAMPO QUE FALTABA
                tipo_muestra=data['tipo_muestra'],
                tipo_analisis=data.get('tipo_analisis'),
                fecha_recoleccion=data['fecha_recoleccion'],
                fecha_entrega=data.get('fecha_entrega'),
                observaciones=data.get('observaciones'),
                tecnico=data.get('tecnico'),
                veterinario_ref=data.get('veterinario_ref'),
                urgente=1 if data.get('urgente') else 0,
                estado='Pendiente',
            )

            muestra_id = self.muestra_repo.create(muestra)
            muestra.id = muestra_id
            logger.info(f"Muestra registrada: {muestra.codigo}")
            return muestra

        except Exception as e:
            logger.error(f"Error en registrar_muestra: {e}")
            raise

    def actualizar_estado(self, muestra_id: int, estado: str,
                          resultado: Optional[str] = None,
                          valor_ref: Optional[str] = None) -> None:
        # RBAC: requiere rol veterinario o superior (cargar resultados
        # es una acción clínica)
        self.authorizer.require_role('veterinario')

        try:
            if estado not in [
                'Pendiente',
                'En Proceso',
                'Completado',
                    'Descartado']:
                raise BusinessLogicError("Estado no válido")
            self.muestra_repo.update_estado(
                muestra_id, estado, resultado, valor_ref)
            logger.info(
                f"Estado de muestra {muestra_id} actualizado a {estado}")
        except Exception as e:
            logger.error(f"Error en actualizar_estado: {e}")
            raise

    def listar_muestras(self, filtros: Optional[Dict] = None) -> List[Muestra]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.muestra_repo.get_all(filtros)

    def obtener_pendientes(self) -> List[Muestra]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.muestra_repo.get_all({'estado': 'Pendiente'})

    def obtener_urgentes(self) -> List[Muestra]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.muestra_repo.get_all({'urgente': True})

    def generar_codigo(self) -> str:
        """Genera código correlativo de manera atómica para laboratorio.

        Fase 6 (S-M5): este método CONSUME el contador (``UPDATE ...
        SET ultimo = ultimo + 1``). Para previsualizar sin consumir
        (útil al abrir el diálogo de muestra), usar
        ``preview_siguiente_codigo``.
        """
        # RBAC: cualquier usuario autenticado puede generar (consumir)
        self.authorizer.require_authenticated()
        return self.db_manager.consumir_codigo('LAB')

    def preview_siguiente_codigo(self) -> str:
        """Retorna el siguiente código LAB-XXXX SIN consumirlo (read-only).

        Fase 6 (S-M5): para que el diálogo de muestra pueda mostrar
        "Próximo código: LAB-0042" al abrir, sin gastar el número si el
        usuario cancela. Antes, ``generar_codigo`` se llamaba al abrir
        el diálogo y al cerrar (dos consumos por cada muestra creada,
        dejando huecos en la secuencia). El flujo correcto ahora es::

            dialog.__init__  →  svc.preview_siguiente_codigo()  # preview
            dialog._on_save  →  svc.consumir_codigo()           # consume

        Coordinado con DB batch (9-a) que hace lo mismo en
        ``AnimalService.obtener_siguiente_codigo``.
        """
        # RBAC: cualquier usuario autenticado puede previsualizar
        self.authorizer.require_authenticated()
        return self.db_manager.preview_siguiente_codigo('LAB')

    def consumir_codigo(self) -> str:
        """Consumo atómico del siguiente código LAB-XXXX.

        Fase 6 (S-M5): alias explícito de ``generar_codigo`` para
        simetría con ``preview_siguiente_codigo``.
        """
        # RBAC: cualquier usuario autenticado puede consumir
        self.authorizer.require_authenticated()
        return self.db_manager.consumir_codigo('LAB')
