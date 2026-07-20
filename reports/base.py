# reports/base.py
"""
Clase base abstracta de la que heredan TODOS los reportes.
Garantiza consistencia en encabezado, pie de página, estilos y estructura.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from .config import (
    config,
    ConfiguracionReporte,
    TipoCliente,
    obtener_config_empresa
)
from .helpers import (
    formatear_fecha,
    formatear_hora,
    generar_codigo_verificacion,
    logo_a_base64,
    imagen_a_base64
)


@dataclass
class MetadatosReporte:
    """Metadatos que viajan con cada reporte generado."""
    id_reporte: str = field(default_factory=lambda: str(uuid4())[:8].upper())
    numero_reporte: str = ""
    fecha_generacion: datetime = field(default_factory=datetime.now)
    usuario_genera: str = ""
    tipo_reporte: str = ""
    tipo_cliente: TipoCliente = TipoCliente.PERSONA_NATURAL
    version_plantilla: str = "1.0"
    codigo_verificacion: str = ""
    observaciones_internas: str = ""
    es_copia: bool = False
    es_borrador: bool = False


class ReporteBase(ABC):
    """
    Clase base abstracta para TODOS los reportes del sistema.

    Toda subclase DEBE implementar:
        - obtener_datos()
        - obtener_template()
        - obtener_titulo()

    Y puede sobreescribir opcionalmente:
        - obtener_subtitulo()
        - obtener_css_adicional()
        - pre_procesar_datos()
        - post_procesar_html()
    """

    def __init__(
        self,
        configuracion: Optional[ConfiguracionReporte] = None,
        tipo_cliente: TipoCliente = TipoCliente.PERSONA_NATURAL,
        datos_cliente: Optional[dict] = None,
        datos_extra: Optional[dict] = None,
        es_borrador: bool = False,
        es_copia: bool = False,
        usuario_genera: str = "Sistema"
    ):
        self.config = configuracion or config
        self.tipo_cliente = tipo_cliente
        self.datos_cliente = datos_cliente or {}
        self.datos_extra = datos_extra or {}
        self.es_borrador = es_borrador
        self.es_copia = es_copia
        self.usuario_genera = usuario_genera
        self.font_config = FontConfiguration()

        # Metadatos
        self.metadatos = MetadatosReporte(
            tipo_reporte=self.__class__.__name__,
            tipo_cliente=tipo_cliente,
            usuario_genera=usuario_genera,
            es_borrador=es_borrador,
            es_copia=es_copia,
            codigo_verificacion=generar_codigo_verificacion()
        )

        # Datos del reporte (se llenan al llamar generar())
        self._datos: dict = {}
        self._html_final: str = ""
        self._pdf_bytes: bytes = b""

    # ==================== MÉTODOS ABSTRACTOS (OBLIGATORIOS) =================

    @abstractmethod
    def obtener_datos(self) -> dict:
        """
        Retorna un diccionario con TODOS los datos necesarios para el template.
        Cada subclase define su propia estructura de datos.
        """

    @abstractmethod
    def obtener_template(self) -> Path:
        """Retorna la ruta al archivo HTML template del reporte."""

    @abstractmethod
    def obtener_titulo(self) -> str:
        """Retorna el título principal del reporte."""

    # ==================== MÉTODOS OPCIONALES (SOBREESCRIBIBLES) =============

    def obtener_subtitulo(self) -> str:
        """Subtítulo del reporte. Por defecto vacío."""
        return ""

    def obtener_css_adicional(self) -> str:
        """CSS adicional específico de este tipo de reporte."""
        return ""

    def obtener_numero_reporte(self) -> str:
        """Genera el número correlativo del reporte. Sobreescribir si tiene lógica especial."""
        fecha = self.metadatos.fecha_generacion
        prefijo = self._obtener_prefijo_numero()
        return f"{prefijo}-{fecha.strftime('%Y%m%d')}-{self.metadatos.id_reporte}"

    def pre_procesar_datos(self, datos: dict) -> dict:
        """Permite modificar los datos antes de enviarlos al template."""
        return datos

    def post_procesar_html(self, html: str) -> str:
        """Permite modificar el HTML final antes de convertir a PDF."""
        return html

    def _obtener_prefijo_numero(self) -> str:
        """Prefijo para el número de reporte según tipo."""
        prefijos = {
            "ReporteLaboratorio": "LAB",
            "ReporteVacunacion": "VAC",
            "ReporteHistoriaClinica": "HC",
            "ReporteCirugia": "CIR",
        }
        return prefijos.get(self.__class__.__name__, "RPT")

    # ==================== MÉTODOS DE CONTEXTO PARA TEMPLATES ================

    def _construir_contexto_base(self) -> dict:
        """
        Construye el diccionario base que SIEMPRE está disponible en todos los templates.
        """
        lab = self.config.laboratorio
        colores = self.config.colores
        tipografia = self.config.tipografia
        margenes = self.config.margenes

        # Datos de logo
        logo_b64 = ""
        if lab.logo_path and lab.logo_path.exists():
            logo_b64 = logo_a_base64(lab.logo_path)

        # Datos de firma
        firma_b64 = ""
        if lab.firma_digital_path and lab.firma_digital_path.exists():
            firma_b64 = imagen_a_base64(lab.firma_digital_path)

        sello_b64 = ""
        if lab.sello_path and lab.sello_path.exists():
            sello_b64 = imagen_a_base64(lab.sello_path)

        # Configuración específica para empresas
        config_empresa = {}
        if self.tipo_cliente == TipoCliente.EMPRESA:
            config_empresa = obtener_config_empresa(self.datos_cliente)

        contexto = {
            # === LABORATORIO ===
            "lab": {
                "nombre": lab.nombre,
                "nombre_comercial": lab.nombre_comercial,
                "slogan": lab.slogan,
                "nit": lab.nit,
                "registro_sanitario": lab.registro_sanitario,
                "direccion": lab.direccion,
                "ciudad": lab.ciudad,
                "departamento": lab.departamento,
                "pais": lab.pais,
                "direccion_completa": f"{lab.direccion}, {lab.ciudad} - {lab.departamento}, {lab.pais}",
                "telefono_principal": lab.telefono_principal,
                "telefono_celular": lab.telefono_celular,
                "whatsapp": lab.whatsapp,
                "email_principal": lab.email_principal,
                "email_resultados": lab.email_resultados,
                "web": lab.web,
                "horario": lab.horario,
                "director_nombre": lab.director_nombre,
                "director_titulo": lab.director_titulo,
                "director_registro": lab.director_registro,
                "director_especialidad": lab.director_especialidad,
                "logo_b64": logo_b64,
                "logo_ancho": lab.logo_ancho_mm,
                "logo_alto": lab.logo_alto_mm,
                "firma_b64": firma_b64,
                "sello_b64": sello_b64,
            },

            # === CLIENTE ===
            "cliente": self.datos_cliente,

            # === METADATOS ===
            "metadatos": {
                "id_reporte": self.metadatos.id_reporte,
                "numero_reporte": self.metadatos.numero_reporte,
                "fecha_generacion": formatear_fecha(self.metadatos.fecha_generacion),
                "hora_generacion": formatear_hora(self.metadatos.fecha_generacion),
                "fecha_hora_generacion": f"{formatear_fecha(self.metadatos.fecha_generacion)} {formatear_hora(self.metadatos.fecha_generacion)}",
                "usuario_genera": self.usuario_genera,
                "tipo_reporte": self.obtener_titulo(),
                "tipo_cliente": self.tipo_cliente.value,
                "version_plantilla": self.metadatos.version_plantilla,
                "codigo_verificacion": self.metadatos.codigo_verificacion,
                "es_copia": self.es_copia,
                "es_borrador": self.es_borrador,
            },

            # === REPORTESPECÍFICO ===
            "titulo": self.obtener_titulo(),
            "subtitulo": self.obtener_subtitulo(),
            "datos": {},  # Se llena con los datos del reporte
            "extra": self.datos_extra,

            # === CONFIGURACIÓN VISUAL ===
            "colores": {
                "primario": colores.primario,
                "primario_oscuro": colores.primario_oscuro,
                "primario_claro": colores.primario_claro,
                "secundario": colores.secundario,
                "secundario_oscuro": colores.secundario_oscuro,
                "secundario_claro": colores.secundario_claro,
                "acento": colores.acento,
                "acento_claro": colores.acento_claro,
                "texto_principal": colores.texto_principal,
                "texto_secundario": colores.texto_secundario,
                "texto_claro": colores.texto_claro,
                "borde": colores.borde,
                "borde_claro": colores.borde_claro,
                "fondo": colores.fondo,
                "fondo_alternado": colores.fondo_alternado,
                "exito": colores.exito,
                "advertencia": colores.advertencia,
                "peligro": colores.peligro,
                "info": colores.info,
            },

            # === TIPOGRAFÍA ===
            "tipografia": {
                "familia_principal": tipografia.familia_principal,
                "familia_monospace": tipografia.familia_monospace,
                "tamano_base": tipografia.tamaño_base,
                "tamano_titulo": tipografia.tamaño_titulo,
                "tamano_subtitulo": tipografia.tamaño_subtitulo,
                "tamano_pequeno": tipografia.tamaño_pequeno,
                "tamano_mini": tipografia.tamaño_mini,
            },

            # === MÁRGENES ===
            "margenes": {
                "superior": margenes.superior,
                "inferior": margenes.inferior,
                "izquierdo": margenes.izquierdo,
                "derecho": margenes.derecho,
            },

            # === CONFIGURACIÓN GLOBAL ===
            "config": {
                "mostrar_codigo_verificacion": self.config.mostrar_codigo_verificacion,
                "mostrar_marca_agua": self.config.mostrar_marca_agua and not self.es_borrador,
                "marca_agua_texto": self.config.marca_agua_texto,
                "marca_agua_opacidad": self.config.marca_agua_opacidad,
                "mostrar_paginacion": self.config.mostrar_paginacion,
                "tipo_papel": self.config.tipo_papel.value,
                "es_empresa": self.tipo_cliente == TipoCliente.EMPRESA,
                **config_empresa,
            },

            # === CSS ADICIONAL ===
            "css_adicional": self.obtener_css_adicional(),
        }

        return contexto

    # ==================== FLUJO PRINCIPAL ====================

    def generar(self) -> bytes:
        """
        Ejecuta el flujo completo de generación del reporte.
        Retorna los bytes del PDF.
        """
        # 1. Asignar número de reporte
        self.metadatos.numero_reporte = self.obtener_numero_reporte()

        # 2. Obtener datos específicos del reporte
        datos_especificos = self.obtener_datos()

        # 3. Pre-procesar datos
        datos_especificos = self.pre_procesar_datos(datos_especificos)

        # 4. Construir contexto completo
        contexto = self._construir_contexto_base()
        contexto["datos"] = datos_especificos
        self._datos = contexto

        # 5. Cargar y renderizar template
        template_path = self.obtener_template()
        html_crudo = self._renderizar_template(template_path, contexto)

        # 6. Envolver en template base (header/footer)
        html_envuelto = self._envolver_en_base(html_crudo, contexto)

        # 7. Post-procesar HTML
        self._html_final = self.post_procesar_html(html_envuelto)

        # 8. Generar PDF
        self._pdf_bytes = self._convertir_a_pdf(self._html_final)

        return self._pdf_bytes

    def generar_y_guardar(
        self,
        nombre_archivo: Optional[str] = None,
        subdirectorio: Optional[str] = None
    ) -> Path:
        """
        Genera el PDF y lo guarda en disco.
        Retorna la ruta del archivo generado.
        """
        pdf_bytes = self.generar()

        if not nombre_archivo:
            nombre_archivo = f"{self.metadatos.numero_reporte}.pdf"

        # Limpiar nombre de archivo
        nombre_archivo = "".join(
            c for c in nombre_archivo
            if c.isalnum() or c in "._- "
        ).strip()

        if subdirectorio:
            output_dir = self.config.output_dir / subdirectorio
        else:
            output_dir = self.config.output_dir

        output_dir.mkdir(parents=True, exist_ok=True)
        ruta_salida = output_dir / nombre_archivo

        ruta_salida.write_bytes(pdf_bytes)

        return ruta_salida

    def previsualizar_html(self) -> str:
        """
        Genera el HTML final sin convertir a PDF.
        Útil para depuración o previsualización en navegador.
        """
        if not self._html_final:
            self.generar()
        return self._html_final

    # ==================== MÉTODOS INTERNOS ====================

    def _renderizar_template(self, template_path: Path, contexto: dict) -> str:
        """Renderiza un template HTML con los datos proporcionados."""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            env = Environment(
                loader=FileSystemLoader(str(template_path.parent)),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # Filtros personalizados
            env.filters['default_if_empty'] = lambda v, d='—': v if v else d
            env.filters['upper'] = lambda v: str(v).upper() if v else ''
            env.filters['lower'] = lambda v: str(v).lower() if v else ''
            env.filters['capitalize_first'] = lambda v: str(
                v).capitalize() if v else ''

            template = env.get_template(template_path.name)
            return template.render(**contexto)

        except ImportError:
            # Fallback si no hay jinja2: reemplazo simple
            html = template_path.read_text(encoding='utf-8')
            return html

    def _envolver_en_base(self, contenido: str, contexto: dict) -> str:
        """Envuelve el contenido del reporte en el template base (con header/footer)."""
        base_template_path = self.config.templates_dir / "base_report.html"

        if not base_template_path.exists():
            # Si no existe base, usar el contenido directamente con estilos
            # mínimos
            return f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <style>{self._obtener_css_base()}</style>
                <style>{contexto.get('css_adicional', '')}</style>
            </head>
            <body>
                {contenido}
            </body>
            </html>
            """

        contexto["contenido_reporte"] = contenido
        return self._renderizar_template(base_template_path, contexto)

    def _obtener_css_base(self) -> str:
        """Carga el CSS base del reporte."""
        css_path = self.config.templates_dir / "styles" / "base.css"
        if css_path.exists():
            return css_path.read_text(encoding='utf-8')
        return ""

    def _convertir_a_pdf(self, html: str) -> bytes:
        """Convierte HTML a PDF usando WeasyPrint.

        Fase 3 (issue C3): usa el ``url_fetcher`` sandboxed de
        ``reports.generators`` para bloquear cualquier recurso externo
        (``http(s)://``, ``ftp://``, ``data:``) y solo permitir
        ``file://`` bajo ``BASE_DIR`` (logos, firmas, sellos, fuentes
        locales). Previene SSRF vía plantillas PDF.
        """
        from reports.generators import _safe_url_fetcher

        documento = HTML(
            string=html,
            url_fetcher=_safe_url_fetcher,
        )
        pdf = documento.render(
            font_config=self.font_config,
            presentational_hints=True
        )
        return pdf.write_pdf()

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"tipo={self.tipo_cliente.value} "
            f"numero={self.metadatos.numero_reporte}>"
        )
