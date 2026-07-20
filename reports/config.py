# reports/config.py
"""
Configuración centralizada de reportes ISALAB.
Toda la personalización de marca, colores y datos del laboratorio va aquí.
"""

from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from typing import Optional
import sys


def _get_bundle_dir() -> Path:
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


class TipoCliente(Enum):
    PERSONA_NATURAL = "persona_natural"
    EMPRESA = "empresa"


class TipoPapel(Enum):
    CARTA = "letter"       # 216mm x 279mm
    OFICIO = "legal"       # 216mm x 356mm
    A4 = "a4"              # 210mm x 297mm


@dataclass
class DatosLaboratorio:
    """Datos completos del laboratorio que aparecen en cada reporte."""
    nombre: str = "ISALAB"
    nombre_comercial: str = "ISALAB Laboratorio Clínico Veterinario"
    slogan: str = "Precisión y compromiso con la salud animal"
    nit: str = "90.123.456-7"
    registro_sanitario: str = "RSV-2024-001234"
    direccion: str = "Calle 45 No. 12-34, Oficina 201"
    ciudad: str = "Bogotá D.C."
    departamento: str = "Cundinamarca"
    pais: str = "Colombia"
    telefono_principal: str = "(601) 234-5678"
    telefono_celular: str = "311 234-5678"
    whatsapp: str = "311 234-5678"
    email_principal: str = "info@isalab.com.co"
    email_resultados: str = "resultados@isalab.com.co"
    web: str = "www.isalab.com.co"
    horario: str = "Lunes a Viernes 7:00 AM - 6:00 PM | Sábados 8:00 AM - 1:00 PM"

    # Director veterinario
    director_nombre: str = "Dra. [Nombre Completo]"
    director_titulo: str = "Médico Veterinario Zootecnista"
    director_registro: str = "MVZ-[Número Registro]"
    director_especialidad: str = "Laboratorio Clínico Veterinario"

    # Logo
    logo_path: Optional[Path] = None
    logo_ancho_mm: float = 35.0
    logo_alto_mm: float = 35.0

    # Firma digital
    firma_digital_path: Optional[Path] = None
    sello_path: Optional[Path] = None


@dataclass
class ColoresMarca:
    """Paleta de colores corporativa - Healthcare Professional."""
    primario: str = "#0891B2"          # Medical Teal
    primario_oscuro: str = "#0E7490"    # Cyan-700
    primario_claro: str = "#E0F2FE"    # Light Cyan
    secundario: str = "#15803D"        # Health Green
    secundario_oscuro: str = "#166534"   # Green-800
    secundario_claro: str = "#D1FAE5"  # Light Green
    acento: str = "#B91C1C"           # Medical Red
    acento_claro: str = "#FEE2E2"      # Light Red
    texto_principal: str = "#0F172A"    # Slate-900
    texto_secundario: str = "#475569"   # Slate-600
    texto_claro: str = "#94A3B8"      # Slate-400
    borde: str = "#CBD5E1"             # Slate-300
    borde_claro: str = "#F1F5F9"      # Slate-100
    fondo: str = "#FFFFFF"             # Blanco
    fondo_alternado: str = "#F0FDFA"   # Mint White
    exito: str = "#15803D"            # Green-700 valores normales
    advertencia: str = "#B45309"     # Amber-700 borderline
    peligro: str = "#B91C1C"          # Red-700 críticos
    info: str = "#0891B2"              # Teal informativo


@dataclass
class Tipografia:
    """Configuración de fuentes - Healthcare Professional."""
    familia_principal: str = "'Segoe UI', 'Century Gothic', Arial, sans-serif"
    familia_monospace: str = "'Consolas', 'Courier New', monospace"
    tamaño_base: float = 10.0           # pt - tamaño base del texto
    tamaño_titulo: float = 14.0
    tamaño_subtitulo: float = 11.0
    tamaño_pequeño: float = 8.0
    tamaño_mini: float = 7.0


@dataclass
class Margenes:
    """Márgenes en milímetros."""
    superior: float = 12.0
    inferior: float = 15.0
    izquierdo: float = 15.0
    derecho: float = 15.0
    encabezado: float = 10.0
    pie_pagina: float = 12.0


@dataclass
class ConfiguracionReporte:
    """Configuración maestra de todos los reportes."""
    laboratorio: DatosLaboratorio = field(default_factory=DatosLaboratorio)
    colores: ColoresMarca = field(default_factory=ColoresMarca)
    tipografia: Tipografia = field(default_factory=Tipografia)
    margenes: Margenes = field(default_factory=Margenes)
    tipo_papel: TipoPapel = TipoPapel.A4
    mostrar_codigo_verificacion: bool = True
    mostrar_marca_agua: bool = True
    marca_agua_texto: str = "ISALAB"
    marca_agua_opacidad: float = 0.04
    mostrar_paginacion: bool = True
    formato_fecha: str = "%d/%m/%Y"
    formato_hora: str = "%I:%M %p"
    formato_fecha_hora: str = "%d/%m/%Y %I:%M %p"

    # Rutas de trabajo
    templates_dir: Path = field(
        default_factory=lambda: _get_bundle_dir() /
        "templates")
    output_dir: Path = field(
        default_factory=lambda: _get_app_dir() /
        "data" /
        "pdfs")
    assets_dir: Path = field(
        default_factory=lambda: _get_bundle_dir() /
        "assets")

    def __post_init__(self):
        """Asegurar que los directorios existen."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Logo por defecto
        if self.laboratorio.logo_path is None:
            logo_default = self.assets_dir / "logo_isalab.png"
            if logo_default.exists():
                self.laboratorio.logo_path = logo_default


# Instancia singleton - se puede sobreescribir desde la app principal
config = ConfiguracionReporte()

# Auto-cargar configuración persistente si existe
try:
    from services.configuracion_service import ConfiguracionService
    _cfg_svc = ConfiguracionService()
    _saved_lab_data = _cfg_svc.cargar_configuracion()
    if _saved_lab_data:
        if "nit" in _saved_lab_data:
            config.laboratorio.nit = _saved_lab_data["nit"]
        if "direccion" in _saved_lab_data:
            config.laboratorio.direccion = _saved_lab_data["direccion"]
        if "telefono_celular" in _saved_lab_data:
            config.laboratorio.telefono_celular = _saved_lab_data["telefono_celular"]
            config.laboratorio.telefono_principal = _saved_lab_data["telefono_celular"]
        if "slogan" in _saved_lab_data:
            config.laboratorio.slogan = _saved_lab_data["slogan"]
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"No se pudo cargar lab_config.json: {e}")


def actualizar_configuracion(
    laboratorio: Optional[dict] = None,
    colores: Optional[dict] = None,
    margenes: Optional[dict] = None,
    **kwargs
) -> ConfiguracionReporte:
    """
    Actualiza la configuración global de reportes.
    Útil para cargar desde base de datos o archivo de configuración.
    """
    if laboratorio:
        for k, v in laboratorio.items():
            if hasattr(config.laboratorio, k):
                setattr(config.laboratorio, k, v)

    if colores:
        for k, v in colores.items():
            if hasattr(config.colores, k):
                setattr(config.colores, k, v)

    if margenes:
        for k, v in margenes.items():
            if hasattr(config.margenes, k):
                setattr(config.margenes, k, v)

    for k, v in kwargs.items():
        if hasattr(config, k):
            setattr(config, k, v)

    return config


def obtener_config_empresa(cliente_data: dict) -> dict:
    """
    Retorna ajustes específicos cuando el cliente es una empresa.
    Las empresas suelen requerir formato más formal y datos adicionales.
    """
    return {
        "mostrar_nit_empresa": True,
        "mostrar_contacto_empresa": True,
        "mostrar_orden_servicio": True,
        "formato_titulo_extendido": True,
        "incluir_resumen_ejecutivo": True,
        "pie_pagina_extendido": True,
        "empresa_razon_social": cliente_data.get("razon_social", ""),
        "empresa_nit": cliente_data.get("nit", ""),
        "empresa_contacto": cliente_data.get("contacto", ""),
        "empresa_cargo": cliente_data.get("cargo", ""),
        "empresa_telefono": cliente_data.get("telefono", ""),
        "empresa_email": cliente_data.get("email", ""),
        "empresa_direccion": cliente_data.get("direccion", ""),
    }
