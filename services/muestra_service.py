# services/muestra_service.py
"""Lógica de negocio para muestras"""

from typing import List, Dict, Optional, Any
from database.repositories import MuestraRepository, AnimalRepository
from database.connection import DatabaseManager
from database.models import Muestra
from utils.validators import MuestraValidator
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger

logger = setup_logger()


class MuestraService:
    def __init__(self):
        self.muestra_repo = MuestraRepository()
        self.animal_repo = AnimalRepository()
        self.db_manager = DatabaseManager()

    def obtener_muestra(self, muestra_id: int) -> Muestra:
        return self.muestra_repo.get_by_id(muestra_id)

    def registrar_muestra(self, data: Dict[str, Any]) -> Muestra:
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
        return self.muestra_repo.get_all(filtros)

    def obtener_pendientes(self) -> List[Muestra]:
        return self.muestra_repo.get_all({'estado': 'Pendiente'})

    def obtener_urgentes(self) -> List[Muestra]:
        return self.muestra_repo.get_all({'urgente': True})

    def generar_codigo(self) -> str:
        """Genera código correlativo de manera atómica para laboratorio."""
        return self.db_manager.generar_codigo('LAB')
