# reports/generators.py
from pathlib import Path
from typing import Union
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


import sys

if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        BASE_DIR = Path(sys._MEIPASS)
    else:
        BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = BASE_DIR / 'templates'

_reportes_disponibles = {}


def registrar_reporte(tipo: str, clase: type):
    """Registra un tipo de reporte para generación por nombre."""
    _reportes_disponibles[tipo] = clase


def generar_reporte(
        clase_o_template: Union[type, str],
        contexto: dict = None,
        **kwargs
) -> bytes:
    """
    Motor híbrido: Soporta tanto clases ReporteBase estrictas
    como renderizado directo de plantillas HTML.
    """
    if isinstance(clase_o_template, str):
        # Modo Directo: Tomamos la plantilla HTML y le inyectamos el
        # diccionario de datos
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        nombre_archivo = f"{clase_o_template}.html" if not clase_o_template.endswith(
            '.html') else clase_o_template
        template = env.get_template(nombre_archivo)

        # Combinamos el contexto explícito con los kwargs
        datos = contexto or {}
        datos.update(kwargs)

        html_renderizado = template.render(**datos)
        return HTML(string=html_renderizado,
                    base_url=str(TEMPLATES_DIR)).write_pdf()
    else:
        # Modo Enterprise: Instanciar la clase heredada de ReporteBase
        reporte = clase_o_template(**kwargs)
        return reporte.generar()


def generar_por_tipo(
        tipo_reporte: str,
        contexto: dict = None,
        **kwargs) -> bytes:
    """Busca la clase registrada, si no la encuentra, asume que es el nombre del template."""
    clase = _reportes_disponibles.get(tipo_reporte)
    if clase:
        return generar_reporte(clase, **kwargs)
    else:
        return generar_reporte(tipo_reporte, contexto=contexto, **kwargs)
