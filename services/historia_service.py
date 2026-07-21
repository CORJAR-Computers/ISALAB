# services/historia_service.py
"""Lógica de negocio — Historia clínica"""

from datetime import datetime
from typing import List, Optional

from database.repositories import HistoriaClinicaRepository, RecepcionRepository
from database.models import HistoriaClinica
from utils.exceptions import ValidationError
from utils.logger import setup_logger

logger = setup_logger()


class HistoriaService:
    def __init__(self):
        self.repo = HistoriaClinicaRepository()
        self.rec_repo = RecepcionRepository()

    def crear_historia(self, data: dict) -> HistoriaClinica:
        self._validar(data)
        historia = HistoriaClinica(
            recepcion_id=int(data['recepcion_id']),
            animal_id=int(data['animal_id']),
            fecha=data.get('fecha') or datetime.now().strftime('%Y-%m-%d'),
            anamnesis=data.get('anamnesis') or None,
            examen_fisico=data.get('examen_fisico') or None,
            temperatura=_float(data.get('temperatura')),
            frecuencia_cardiaca=_int(data.get('frecuencia_cardiaca')),
            frecuencia_respiratoria=_int(data.get('frecuencia_respiratoria')),
            peso_consulta=_float(data.get('peso_consulta')),
            dieta=data.get('dieta') or None,
            enfermedades_previas=data.get('enfermedades_previas') or None,
            cirugias_previas=data.get('cirugias_previas') or None,
            esterilizado=data.get('esterilizado') or None,
            numero_partos=_int(data.get('numero_partos')),
            esquema_vacunal=data.get('esquema_vacunal') or None,
            ultima_desparasitacion=data.get('ultima_desparasitacion') or None,
            tratamientos_recientes=data.get('tratamientos_recientes') or None,
            viajes_recientes=data.get('viajes_recientes') or None,
            convive_con_animales=data.get('convive_con_animales') or None,
            comportamiento=data.get('comportamiento') or None,
            condicion_corporal=data.get('condicion_corporal') or None,
            tllc=data.get('tllc') or None,
            trpc=data.get('trpc') or None,
            mucosas=data.get('mucosas') or None,
            pulso=data.get('pulso') or None,
            deshidratacion=data.get('deshidratacion') or None,
            diagnostico=data.get('diagnostico') or None,
            diagnostico_diferencial=data.get('diagnostico_diferencial') or None,
            tratamiento=data.get('tratamiento') or None,
            pronostico=data.get('pronostico') or None,
            veterinario=data.get('veterinario', '').strip() or None,
        )
        historia.id = self.repo.create(historia)
        logger.info(
            f"Historia clínica {
                historia.id} para animal {
                historia.animal_id}")
        return historia

    def obtener_historia(self, hid: int) -> HistoriaClinica:
        return self.repo.get_by_id(hid)

    def historias_por_paciente(self, animal_id: int) -> List[HistoriaClinica]:
        return self.repo.get_by_animal(animal_id)

    def historia_de_recepcion(
            self,
            recepcion_id: int) -> Optional[HistoriaClinica]:
        return self.repo.get_by_recepcion(recepcion_id)

    def actualizar_historia(self, hid: int, data: dict) -> None:
        h = self.repo.get_by_id(hid)
        # Usamos 'in data' para distinguir "campo no enviado" de "campo vacío intencionalmente".
        # Esto permite al usuario limpiar campos (enviando cadena vacía) sin perder datos
        # por el efecto de `or` que trataba '' y 0 como falsy.
        if 'anamnesis' in data:
            h.anamnesis = data['anamnesis'] or None
        if 'examen_fisico' in data:
            h.examen_fisico = data['examen_fisico'] or None
        if 'temperatura' in data:
            h.temperatura = _float(data['temperatura'])
        if 'frecuencia_cardiaca' in data:
            h.frecuencia_cardiaca = _int(data['frecuencia_cardiaca'])
        if 'frecuencia_respiratoria' in data:
            h.frecuencia_respiratoria = _int(data['frecuencia_respiratoria'])
        if 'peso_consulta' in data:
            h.peso_consulta = _float(data['peso_consulta'])
        if 'dieta' in data:
            h.dieta = data['dieta'] or None
        if 'enfermedades_previas' in data:
            h.enfermedades_previas = data['enfermedades_previas'] or None
        if 'cirugias_previas' in data:
            h.cirugias_previas = data['cirugias_previas'] or None
        if 'esterilizado' in data:
            h.esterilizado = data['esterilizado'] or None
        if 'numero_partos' in data:
            h.numero_partos = _int(data['numero_partos'])
        if 'esquema_vacunal' in data:
            h.esquema_vacunal = data['esquema_vacunal'] or None
        if 'ultima_desparasitacion' in data:
            h.ultima_desparasitacion = data['ultima_desparasitacion'] or None
        if 'tratamientos_recientes' in data:
            h.tratamientos_recientes = data['tratamientos_recientes'] or None
        if 'viajes_recientes' in data:
            h.viajes_recientes = data['viajes_recientes'] or None
        if 'convive_con_animales' in data:
            h.convive_con_animales = data['convive_con_animales'] or None
        if 'comportamiento' in data:
            h.comportamiento = data['comportamiento'] or None
        if 'condicion_corporal' in data:
            h.condicion_corporal = data['condicion_corporal'] or None
        if 'tllc' in data:
            h.tllc = data['tllc'] or None
        if 'trpc' in data:
            h.trpc = data['trpc'] or None
        if 'mucosas' in data:
            h.mucosas = data['mucosas'] or None
        if 'pulso' in data:
            h.pulso = data['pulso'] or None
        if 'deshidratacion' in data:
            h.deshidratacion = data['deshidratacion'] or None
        if 'diagnostico' in data:
            h.diagnostico = data['diagnostico'] or None
        if 'diagnostico_diferencial' in data:
            h.diagnostico_diferencial = data['diagnostico_diferencial'] or None
        if 'tratamiento' in data:
            h.tratamiento = data['tratamiento'] or None
        if 'pronostico' in data:
            h.pronostico = data['pronostico'] or None
        if 'veterinario' in data:
            h.veterinario = data['veterinario'] or None
        self.repo.update(h)
        logger.info(f"Historia clínica {hid} actualizada")

    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('recepcion_id'):
            errores.append("La recepción es obligatoria")
        if not data.get('animal_id'):
            errores.append("El paciente es obligatorio")
        if errores:
            raise ValidationError(
                "Datos de historia clínica inválidos", {
                    'errores': errores})


# ── helpers de conversión segura ──────────────────────────────────────────
def _float(val) -> Optional[float]:
    """Convierte a float. Solo None y '' se consideran 'sin valor'.
    Un valor de 0.0 es válido (ej. temperatura en Celsius)."""
    if val is None or val == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _int(val) -> Optional[int]:
    """Convierte a int. Solo None y '' se consideran 'sin valor'.
    Un valor de 0 es válido."""
    if val is None or val == '':
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
