# services/report_historia_clinica.py
"""Puente ORM → ReporteBase para historias clínicas completas."""

from typing import Optional, Dict, Any, List

from database.models import HistoriaClinica, Consulta, Vacunacion
from database.repositories import (
    HistoriaClinicaRepository,
    AnimalRepository,
    ConsultaRepository,
    VacunacionRepository,
)
from reports import (
    generar_reporte,
    generar_por_tipo,
    formatear_fecha,
    generar_codigo_verificacion,
    generar_codigo_barras_base64,
    generar_qr_base64,
    imagen_a_base64,
    calcular_edad,
    DatosLaboratorio,
)
from utils.logger import setup_logger

logger = setup_logger()


class ReporteHistoriaClinicaService:
    """Genera PDFs de historia clínica completa (con consultas de seguimiento)."""

    def __init__(self):
        self.historia_repo = HistoriaClinicaRepository()
        self.animal_repo = AnimalRepository()
        self.consulta_repo = ConsultaRepository()
        self.vacuna_repo = VacunacionRepository()
        self.lab = DatosLaboratorio()

    # ── API pública ──────────────────────────────────────────────────────

    def generar_pdf(
        self,
        historia_id: int,
        incluir_consultas: bool = True,
        incluir_vacunas: bool = False,
    ) -> bytes:
        contexto = self._construir_contexto(
            historia_id, incluir_consultas, incluir_vacunas
        )
        return generar_reporte("historia_clinica", contexto)

    def generar_y_guardar(
        self,
        historia_id: int,
        ruta_salida: str,
        incluir_consultas: bool = True,
        incluir_vacunas: bool = False,
    ) -> str:
        contexto = self._construir_contexto(
            historia_id, incluir_consultas, incluir_vacunas
        )
        return generar_por_tipo("historia_clinica", contexto, ruta_salida)

    # ── Contexto ─────────────────────────────────────────────────────────

    def _construir_contexto(
        self,
        historia_id: int,
        incluir_consultas: bool,
        incluir_vacunas: bool,
    ) -> Dict[str, Any]:
        historia = self.historia_repo.get_by_id(historia_id)
        animal = self.animal_repo.get_by_id(historia.animal_id)

        # Consultas de seguimiento (posteriores a esta historia)
        consultas: List[Consulta] = []
        if incluir_consultas:
            todas = self.consulta_repo.get_by_animal(historia.animal_id)
            consultas = [
                c for c in todas
                if c.fecha >= historia.fecha
            ]

        # Esquema de vacunación
        vacunas: List[Vacunacion] = []
        if incluir_vacunas:
            vacunas = self.vacuna_repo.get_by_animal(historia.animal_id)

        # Signos vitales formateados
        signos = self._formatear_signos(historia)

        # Pronóstico badge
        pronostico = self._badge_pronostico(historia.pronostico)

        # Verificación
        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)
        firma = imagen_a_base64("data/imagenes/firma.png")
        sello = imagen_a_base64("data/imagenes/sello.png")

        return {
            "lab": self.lab,
            # Historia
            "historia": historia,
            "fecha": formatear_fecha(historia.fecha),
            "recepcion_codigo": getattr(historia, "recepcion_codigo", None),
            # Paciente
            "animal": animal,
            "edad_texto": calcular_edad(animal.fecha_ingreso),
            # Signos vitales
            "signos": signos,
            # Secciones clínicas
            "anamnesis": historia.anamnesis or "No registrada",
            "examen_fisico": historia.examen_fisico or "No registrado",
            "diagnostico": historia.diagnostico or "No registrado",
            "diagnostico_diferencial": historia.diagnostico_diferencial or "",
            "tiene_dx_diferencial": bool(historia.diagnostico_diferencial),
            "tratamiento": historia.tratamiento or "No registrado",
            "pronostico": pronostico,
            # Consultas de seguimiento
            "consultas": [
                self._formatear_consulta(c) for c in consultas
            ],
            "tiene_consultas": len(consultas) > 0,
            # Vacunas
            "vacunas": [
                {
                    "fecha": formatear_fecha(v.fecha_aplicacion),
                    "producto": v.producto,
                    "tipo": v.tipo,
                    "lote": v.lote or "—",
                }
                for v in vacunas
            ],
            "tiene_vacunas": len(vacunas) > 0,
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Firmas
            "firma_base64": firma,
            "sello_base64": sello,
            "veterinario_nombre": historia.veterinario or "—",
        }

    # ── Helpers internos ─────────────────────────────────────────────────

    @staticmethod
    def _formatear_signos(h: HistoriaClinica) -> Dict[str, Optional[str]]:
        """Formatea los signos vitales, mostrando '—' para nulos."""
        return {
            "temperatura": f"{h.temperatura} °C" if h.temperatura else "—",
            "fc": f"{h.frecuencia_cardiaca} lpm" if h.frecuencia_cardiaca else "—",
            "fr": f"{h.frecuencia_respiratoria} rpm" if h.frecuencia_respiratoria else "—",
            "peso": f"{h.peso_consulta} kg" if h.peso_consulta else "—",
        }

    @staticmethod
    def _badge_pronostico(pronostico: Optional[str]) -> Dict[str, str]:
        if not pronostico:
            return {"texto": "No definido", "css": "pronostico-sin"}
        p = pronostico.strip().lower()
        mapa = {
            "bueno": ("Bueno", "pronostico-bueno"),
            "favorable": ("Favorable", "pronostico-bueno"),
            "reservado": ("Reservado", "pronostico-reservado"),
            "grave": ("Grave", "pronostico-grave"),
            "desfavorable": ("Desfavorable", "pronostico-grave"),
            "fatal": ("Fatal", "pronostico-grave"),
        }
        texto, css = mapa.get(p, (pronostico.strip(), "pronostico-sin"))
        return {"texto": texto, "css": css}

    @staticmethod
    def _formatear_consulta(c: Consulta) -> Dict[str, Any]:
        return {
            "codigo": c.codigo,
            "fecha": formatear_fecha(c.fecha),
            "motivo": c.motivo or "—",
            "evolucion": c.evolucion or "",
            "examen_fisico": c.examen_fisico or "",
            "tratamiento": c.tratamiento or "",
            "medicamentos": c.medicamentos or "",
            "veterinario": c.veterinario or "—",
            "proxima_consulta": (
                formatear_fecha(c.proxima_consulta)
                if c.proxima_consulta else None
            ),
        }
