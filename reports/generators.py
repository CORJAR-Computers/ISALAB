# reports/generators.py
"""
Motor de generación de reportes — ISALAB.

Fase 3 (issue C3 — CRÍTICO de seguridad):
    Antes, ``Environment(loader=FileSystemLoader(...))`` se construía SIN
    ``autoescape``, lo que permitía inyección HTML/JS a través de
    cualquier campo controlado por el usuario (``animal.nombre``,
    ``propietario``, ``diagnostico``, ``observaciones``, etc.). El PDF
    generado por WeasyPrint podía incrustar ``<script>``, ``<iframe>``,
    o peor, etiquetas ``<img src=...>``/``<link href=...>`` que disparaban
    peticiones HTTP externas (SSRF) al renderizar.

    Ahora:
    1. ``Environment`` se crea con ``select_autoescape(['html', 'xml'])``.
    2. ``trim_blocks``/``lstrip_blocks`` para limpiar whitespace.
    3. ``HTML(...).write_pdf(url_fetcher=_safe_url_fetcher)`` restringe
       los recursos que WeasyPrint puede fetchear: SOLO ``file://``
       bajo ``TEMPLATES_DIR``. Cualquier URL ``http(s)://`` externa o
       archivo fuera del sandbox se rechaza.
"""
from pathlib import Path
from typing import Union
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, select_autoescape
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


# ─────────────────────────────────────────────────────────────────────────────
# Sandbox de recursos (Fase 3 — issue C3 SSRF / HTML injection)
# ─────────────────────────────────────────────────────────────────────────────

def _safe_url_fetcher(url: str, timeout: int = 10, ssl_context=None):
    """
    ``url_fetcher`` para WeasyPrint que RECHAZA cualquier recurso externo.

    WeasyPrint pide al ``url_fetcher`` resolver TODO: CSS ``@import``,
    ``url()``, ``<img src>``, ``<link>``, fuentes ``@font-face``, etc.

    Política:
      - ``file://`` permitido SOLO si el path está bajo ``TEMPLATES_DIR``
        o ``BASE_DIR`` (logos, firmas, sellos, fuentes locales).
      - Todo lo demás (``http://``, ``https://``, ``ftp://``, ``data:``)
        se rechaza con ``ValueError``. WeasyPrint lo registra como
        recurso no disponible y sigue renderizando el PDF sin ese
        recurso, en lugar de hacer una petición de red.
    """
    import logging
    sandbox_logger = logging.getLogger("isalab.reports.sandbox")

    parsed = urlparse(url)
    scheme = (parsed.scheme or '').lower()

    if scheme == 'file':
        # Resolver path absoluto del archivo solicitado
        try:
            local_path = Path(parsed.path).resolve()
        except (OSError, ValueError):
            sandbox_logger.warning(
                f"[sandbox] path inválido rechazado: {url}"
            )
            raise ValueError(f"URL no permitida: {url}")

        # Solo permitir archivos bajo TEMPLATES_DIR o BASE_DIR
        try:
            local_path.relative_to(TEMPLATES_DIR.resolve())
            allowed = True
        except ValueError:
            try:
                local_path.relative_to(BASE_DIR.resolve())
                allowed = True
            except ValueError:
                allowed = False

        if not allowed:
            sandbox_logger.warning(
                f"[sandbox] file fuera del sandbox rechazado: {url}"
            )
            raise ValueError(
                f"Archivo fuera del sandbox permitido: {url}"
            )

        # Delegar al fetcher por defecto de WeasyPrint para file://
        from weasyprint.default_url_fetcher import fetch
        return fetch(url, timeout=timeout, ssl_context=ssl_context)

    # Cualquier otro esquema (http, https, ftp, data) → rechazar
    sandbox_logger.warning(
        f"[sandbox] recurso externo rechazado: {url}"
    )
    raise ValueError(
        f"Recurso externo no permitido en PDF: {url}. "
        f"Solo se permiten archivos locales bajo {TEMPLATES_DIR}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────

def registrar_reporte(tipo: str, clase: type):
    """Registra un tipo de reporte para generación por nombre."""
    _reportes_disponibles[tipo] = clase


def _build_jinja_env() -> Environment:
    """Construye un Environment Jinja2 con autoescape SIEMPRE activo."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        # CRÍTICO: autoescape para HTML/XML previene inyección.
        autoescape=select_autoescape(['html', 'xml', 'htm']),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generar_reporte(
        clase_o_template: Union[type, str],
        contexto: dict = None,
        **kwargs
) -> bytes:
    """
    Motor híbrido: Soporta tanto clases ReporteBase estrictas
    como renderizado directo de plantillas HTML.

    Fase 3: SIEMPRE usa autoescape + url_fetcher sandboxed.
    """
    if isinstance(clase_o_template, str):
        # Modo Directo: Tomamos la plantilla HTML y le inyectamos el
        # diccionario de datos
        env = _build_jinja_env()
        nombre_archivo = f"{clase_o_template}.html" if not clase_o_template.endswith(
            '.html') else clase_o_template
        template = env.get_template(nombre_archivo)

        # Combinamos el contexto explícito con los kwargs
        datos = contexto or {}
        datos.update(kwargs)

        html_renderizado = template.render(**datos)
        return HTML(
            string=html_renderizado,
            base_url=str(TEMPLATES_DIR),
            url_fetcher=_safe_url_fetcher,
        ).write_pdf()
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
