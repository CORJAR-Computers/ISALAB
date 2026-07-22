# reports.py
"""Motor de generacion de reportes PDF para IsaLab.

Puente entre los servicios (ORM) y las plantillas Jinja2 + WeasyPrint.
"""

import os
import sys
import base64
import secrets
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from utils.logger import setup_logger

logger = setup_logger()

# ── Rutas ────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    if hasattr(sys, "_MEIPASS"):
        _BASE = Path(sys._MEIPASS)
    else:
        _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).resolve().parent

TEMPLATES_DIR = _BASE / "templates"


@dataclass
class DatosLaboratorio:
    """Informacion institucional para todos los reportes."""
    nombre: str = "IsaLab"
    nombre_comercial: str = "IsaLab - Centro Diagnostico Veterinario"
    nit: str = ""
    direccion: str = ""
    direccion_completa: str = ""
    telefono_principal: str = ""
    email_principal: str = ""
    web: str = ""
    logo_path: str = ""


@dataclass
class ColoresMarca:
    primario: str = "#1B5E7B"
    primario_oscuro: str = "#0D3B4F"
    primario_claro: str = "#E8F4F8"
    secundario: str = "#2ECC71"
    secundario_oscuro: str = "#27AE60"
    secundario_claro: str = "#E8F8F0"
    acento: str = "#E74C3C"
    acento_claro: str = "#FDEDEC"
    texto_principal: str = "#2C3E50"
    texto_secundario: str = "#5D6D7E"
    texto_claro: str = "#95A5A6"
    borde: str = "#BDC3C7"
    borde_claro: str = "#ECF0F1"
    fondo: str = "#FFFFFF"
    fondo_alternado: str = "#F8F9FA"
    exito: str = "#27AE60"
    advertencia: str = "#F39C12"
    peligro: str = "#E74C3C"
    info: str = "#3498DB"


@dataclass
class ConfiguracionReporte:
    tipo_papel: str = "a4"
    mostrar_marca_agua: bool = True
    marca_agua_texto: str = "ISALAB"
    marca_agua_opacidad: float = 0.04
    mostrar_codigo_verificacion: bool = True
    mostrar_paginacion: bool = True


@dataclass
class Margenes:
    superior: float = 12.0
    inferior: float = 15.0
    izquierdo: float = 15.0
    derecho: float = 15.0
    encabezado: float = 10.0
    pie_pagina: float = 12.0


# ── Jinja2 environment (reutilizado) ────────────────────────────────
_jinja_env: Optional[Environment] = None


def _get_jinja_env() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _jinja_env


def generar_reporte(tipo: str, contexto: Dict[str, Any]) -> bytes:
    """Genera un PDF y retorna los bytes."""
    html_str = _render_html(tipo, contexto)
    return _html_to_pdf(html_str)


def generar_por_tipo(tipo: str, contexto: Dict[str, Any], ruta_salida: str) -> str:
    """Genera un PDF y lo guarda en disco. Retorna la ruta."""
    html_str = _render_html(tipo, contexto)
    pdf_bytes = _html_to_pdf(html_str)
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(pdf_bytes)
    logger.info(f"PDF guardado: {ruta}")
    return str(ruta)


def formatear_fecha(fecha_str: Optional[str]) -> str:
    if not fecha_str:
        return "-"
    fecha_limpia = fecha_str.split(" ")[0].split("T")[0]
    try:
        dt = datetime.strptime(fecha_limpia, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(fecha_str) if fecha_str else "-"


def calcular_edad(fecha_str: Optional[str]) -> str:
    if not fecha_str:
        return "-"
    fecha_limpia = fecha_str.split(" ")[0].split("T")[0]
    try:
        dt = datetime.strptime(fecha_limpia, "%Y-%m-%d")
        hoy = datetime.now()
        anos = hoy.year - dt.year
        meses = hoy.month - dt.month
        if meses < 0:
            anos -= 1
            meses += 12
        if anos > 0:
            return f"{anos} ano(s) y {meses} mes(es)"
        elif meses > 0:
            return f"{meses} mes(es)"
        else:
            dias = (hoy - dt).days
            return f"{dias} dia(s)"
    except (ValueError, TypeError):
        return "-"


def calcular_edad_anios(fecha_str: Optional[str]) -> str:
    if not fecha_str:
        return "-"
    fecha_limpia = fecha_str.split(" ")[0].split("T")[0]
    try:
        dt = datetime.strptime(fecha_limpia, "%Y-%m-%d")
        anos = datetime.now().year - dt.year
        if (datetime.now().month, datetime.now().day) < (dt.month, dt.day):
            anos -= 1
        return f"{anos}" if anos >= 0 else "-"
    except (ValueError, TypeError):
        return "-"


def generar_codigo_verificacion(longitud: int = 12) -> str:
    return secrets.token_hex(longitud // 2).upper()[:longitud]


def generar_codigo_barras_base64(codigo: str, ancho: int = 200, alto: int = 60) -> str:
    try:
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO
        Code128 = barcode.get_barcode_class("code128")
        bar = Code128(codigo, writer=ImageWriter())
        buffer = BytesIO()
        bar.write(buffer, options={"write_text": False, "module_width": 0.4})
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        logger.warning("python-barcode no disponible, generando placeholder")
        return _placeholder_barcode_base64(codigo, ancho, alto)


def generar_qr_base64(codigo: str, tamano: int = 120) -> str:
    try:
        import qrcode
        from io import BytesIO
        qr = qrcode.QRCode(
            version=2, error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5, border=2,
        )
        qr.add_data(codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        logger.warning("qrcode no disponible")
        return ""


def imagen_a_base64(ruta: str) -> str:
    if not ruta:
        return ""
    path = Path(ruta)
    if not path.is_absolute():
        path = _BASE / ruta
    if not path.exists():
        return ""
    try:
        ext = path.suffix.lstrip(".").lower()
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/png")
        data = path.read_bytes()
        return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error convirtiendo imagen {path}: {e}")
        return ""


def formatear_valor_numerico(valor) -> str:
    if valor is None or valor == "":
        return "-"
    try:
        v = float(valor)
        if v == int(v):
            return str(int(v))
        return f"{v:.2f}"
    except (ValueError, TypeError):
        return str(valor)


def clasificar_valor(valor, ref_min, ref_max) -> str:
    try:
        v = float(valor)
        if ref_min is not None and ref_max is not None:
            if v < float(ref_min):
                return "bajo"
            elif v > float(ref_max):
                return "alto"
        return "normal"
    except (ValueError, TypeError):
        return "normal"


def _render_html(tipo: str, contexto: Dict[str, Any]) -> str:
    env = _get_jinja_env()
    template_name = f"{tipo}.html"
    defaults = {
        "lab": contexto.get("lab", DatosLaboratorio()),
        "colores": contexto.get("colores", ColoresMarca()),
        "config": contexto.get("config", ConfiguracionReporte()),
        "margenes": contexto.get("margenes", Margenes()),
        "metadatos": contexto.get("metadatos", {
            "titulo": f"Reporte - {tipo}",
            "es_borrador": False,
            "es_copia": False,
        }),
        "tipografia": contexto.get("tipografia", {
            "titulo": "Arial, sans-serif",
            "normal": "Arial, sans-serif",
            "monospace": "Courier New, monospace",
        }),
    }
    ctx = {**defaults, **contexto}
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception as e:
        logger.error(f"Error renderizando plantilla '{template_name}': {e}")
        raise


def _html_to_pdf(html_str: str) -> bytes:
    try:
        html = HTML(string=html_str, base_url=str(TEMPLATES_DIR))
        return html.write_pdf()
    except Exception as e:
        logger.error(f"Error generando PDF con WeasyPrint: {e}")
        raise


def _placeholder_barcode_base64(codigo: str, ancho: int, alto: int) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="50%" y="55%" text-anchor="middle" '
        f'font-family="monospace" font-size="10" fill="#333">'
        f'{codigo}</text></svg>'
    )
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"
