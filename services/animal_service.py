# services/animal_service.py
"""Lógica de negocio para animales"""

from typing import List, Dict, Optional, Any
from database.repositories import AnimalRepository, MovimientoRepository
# <-- Necesario para generar códigos seguros
from database.connection import DatabaseManager
from database.models import Animal, Movimiento
from utils.exceptions import BusinessLogicError, DuplicateError
from utils.logger import setup_logger
from schemas.animal import AnimalSchema
from pydantic import ValidationError

logger = setup_logger()


class AnimalService:
    def __init__(self):
        self.animal_repo = AnimalRepository()
        self.movimiento_repo = MovimientoRepository()
        self.db_manager = DatabaseManager()  # Para el generador de códigos

    def obtener_siguiente_codigo(self) -> str:
        """Usa el contador atómico de la BD para evitar colisiones si borran registros."""
        return self.db_manager.generar_codigo('PAC')

    def obtener_animal(self, animal_id: int) -> Animal:
        return self.animal_repo.get_by_id(animal_id)

    def registrar_ingreso(self, data: Dict[str, Any]) -> Animal:
        try:
            # 1. Validamos con Pydantic.
            # NOTA: Asegúrate de tener configurado extra="ignore" en tu
            # AnimalSchema
            datos_validados = AnimalSchema(**data)

            if self.animal_repo.get_by_codigo(datos_validados.codigo):
                raise DuplicateError(
                    f"Ya existe un animal con el código {
                        datos_validados.codigo}")

            # 2. Mapeo COMPLETO de todos los campos que envía la UI
            animal = Animal(
                codigo=datos_validados.codigo.upper(),
                nombre=datos_validados.nombre,
                especie=datos_validados.especie,
                raza=datos_validados.raza,
                edad=datos_validados.edad,
                peso=datos_validados.peso,
                propietario=datos_validados.propietario,
                telefono=datos_validados.telefono,
                email=datos_validados.email,
                fecha_ingreso=datos_validados.fecha_ingreso,
                observaciones=datos_validados.observaciones,
                estado=datos_validados.estado,

                # --- CAMPOS NUEVOS QUE ANTES SE PERDÍAN ---
                microchip=_vn(data.get('microchip')),
                sexo=_vn(data.get('sexo')),
                color=_vn(data.get('color')),
                tipo_pelo=_vn(data.get('tipo_pelo')),
                senas_particulares=_vn(data.get('senas_particulares')),
                fecha_nacimiento=_vn(data.get('fecha_nacimiento')),
                unidad_edad=_vn(data.get('unidad_edad')),

                propietario_tipo_doc=_vn(data.get('propietario_tipo_doc')),
                propietario_documento=_vn(data.get('propietario_documento')),
                propietario_direccion=_vn(data.get('propietario_direccion')),
                propietario_oficio=_vn(data.get('propietario_oficio')),
                # -------------------------------------------
            )

            animal_id = self.animal_repo.create(animal)
            animal.id = animal_id

            movimiento = Movimiento(
                animal_id=animal_id,
                tipo='Entrada',
                motivo=data.get('motivo_ingreso', 'Ingreso inicial'),
                responsable=data.get('responsable', 'Sistema'),
            )
            self.movimiento_repo.create(movimiento)

            logger.info(f"Ingreso registrado: {animal.codigo}")
            return animal

        except ValidationError as e:
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            logger.error(f"Error de validación Pydantic: {error_msg}")
            raise BusinessLogicError(f"Datos inválidos:\n{error_msg}")
        except Exception as e:
            logger.error(f"Error en registrar_ingreso: {e}")
            raise

    def registrar_salida(self, animal_id: int, data: Dict[str, Any]) -> None:
        try:
            animal = self.animal_repo.get_by_id(animal_id)
            if animal.estado == 'Dado de Alta':
                raise BusinessLogicError(
                    "El animal ya fue dado de alta anteriormente")
            if not data.get('motivo'):
                raise BusinessLogicError("El motivo de salida es obligatorio")
            if not data.get('responsable'):
                raise BusinessLogicError("El responsable es obligatorio")

            movimiento = Movimiento(
                animal_id=animal_id,
                tipo='Salida',
                motivo=data['motivo'],
                responsable=data['responsable'],
                destino=data.get('destino'),
            )
            self.movimiento_repo.create(movimiento)
            self.animal_repo.update_estado(animal_id, 'Dado de Alta')
            logger.info(f"Salida registrada: Animal {animal_id}")

        except Exception as e:
            logger.error(f"Error en registrar_salida: {e}")
            raise

    def actualizar_datos(self, animal_id: int, data: Dict[str, Any]) -> Animal:
        try:
            animal = self.animal_repo.get_by_id(animal_id)
            data['codigo'] = animal.codigo  # Inyectamos el código

            datos_validados = AnimalSchema(**data)

            # Mapeo COMPLETO para la actualización también
            animal.nombre = datos_validados.nombre
            animal.especie = datos_validados.especie
            animal.raza = datos_validados.raza
            animal.edad = datos_validados.edad
            animal.peso = datos_validados.peso
            animal.propietario = datos_validados.propietario
            animal.telefono = datos_validados.telefono
            animal.email = datos_validados.email
            animal.estado = datos_validados.estado
            animal.observaciones = datos_validados.observaciones

            # --- NUEVOS CAMPOS ---
            animal.microchip = _vn(data.get('microchip'))
            animal.sexo = _vn(data.get('sexo'))
            animal.color = _vn(data.get('color'))
            animal.tipo_pelo = _vn(data.get('tipo_pelo'))
            animal.senas_particulares = _vn(data.get('senas_particulares'))
            animal.fecha_nacimiento = _vn(data.get('fecha_nacimiento'))
            animal.unidad_edad = _vn(data.get('unidad_edad'))
            animal.propietario_tipo_doc = _vn(data.get('propietario_tipo_doc'))
            animal.propietario_documento = _vn(data.get('propietario_documento'))
            animal.propietario_direccion = _vn(data.get('propietario_direccion'))
            animal.propietario_oficio = _vn(data.get('propietario_oficio'))
            # ----------------------

            self.animal_repo.update(animal)
            return animal

        except ValidationError as e:
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            raise BusinessLogicError(f"Datos inválidos:\n{error_msg}")
        except Exception as e:
            logger.error(f"Error en actualizar_datos: {e}")
            raise

    def listar_animales(self, filtros: Optional[Dict] = None, limit: Optional[int] = 50, offset: Optional[int] = 0) -> List[Animal]:
        return self.animal_repo.get_all(filtros, limit=limit, offset=offset)

    def obtener_historial(self, animal_id: int) -> List[Movimiento]:
        return self.movimiento_repo.get_by_animal(animal_id)



def _vn(val):
    if isinstance(val, str) and val.strip() == '':
        return None
    return val
