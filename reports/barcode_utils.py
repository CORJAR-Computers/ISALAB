# reports/barcode_utils.py
"""
Generación de códigos de barras y QR para reportes.
Configurado específicamente para ReportLab 4+ (evita el error de Cairo)
"""

from utils.logger import setup_logger
from reportlab.graphics import renderPM
from reportlab.lib import colors as rl_colors
from reportlab.graphics.barcode import createBarcodeDrawing
from typing import Optional
import io
import base64
import os

# Forzar a ReportLab a usar Pillow (PIL) en lugar de buscar Cairo (rlPyCairo)
os.environ['RENDERPM_BACKEND'] = 'PIL'


logger = setup_logger()


def generar_codigo_barras_base64(
        datos: str,
        tipo: str = "Code128",
        ancho: int = 300,
        alto: int = 50,
        fondo: str = "#FFFFFF",
        color_lineas: str = "#000000"
) -> str:
    """
    Genera un código de barras y lo retorna como imagen base64 (data URI).

    El código de barras se genera con barras gruesas y altas para buena
    legibilidad en PDF. NO se fuerzan dimensiones del Drawing para evitar
    que el barcode quede arrinconado con espacio en blanco.
    """
    if not datos:
        return ""

    try:
        color_fondo = rl_colors.HexColor(fondo)
        color_linea = rl_colors.HexColor(color_lineas)

        # Crear el código de barras con barras gruesas y altas
        barcode = createBarcodeDrawing(
            tipo,
            value=datos,
            barWidth=1.5,              # Barras gruesas para buena visibilidad
            barHeight=alto * 0.85,
            # Barras altas (aprovechan el alto disponible)
            barFillColor=color_linea,
            backColor=color_fondo
        )

        # NO forzar barcode.width / barcode.height
        # El Drawing se auto-dimensiona al contenido del barcode.
        # Forzar dimensiones creaba un lienzo grande con el barcode
        # arrinconado.

        # Renderizar a PNG usando el backend Pillow
        img_buffer = io.BytesIO()
        renderPM.drawToFile(barcode, img_buffer, fmt='PNG', dpi=150)
        img_buffer.seek(0)

        b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    except Exception as e:
        logger.error(f"Error generando código de barras: {e}")
        return ""


def generar_qr_base64(
        datos: str,
        tamaño: int = 150,
        color: str = "#000000",
        fondo: str = "#FFFFFF"
) -> str:
    """
    Genera un código QR y lo retorna como imagen base64 (data URI).

    Método principal: librería 'qrcode' (pura Python, sin dependencia de Cairo).
    Método fallback: ReportLab QrCodeWidget + renderPM.
    """
    if not datos:
        return ""

    # ── Método 1: librería qrcode (recomendada, más robusta) ──
    try:
        import qrcode

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(datos)
        qr.make(fit=True)

        img = qr.make_image(fill_color=color, back_color=fondo)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    except Exception as e:
        logger.warning(f"qrcode lib falló, intentando ReportLab: {e}")

    # ── Método 2: ReportLab QrCodeWidget (fallback) ──
    try:
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing

        qr_widget = QrCodeWidget(datos)
        # El QrCodeWidget necesita dimensiones explícitas
        qr_size = tamaño
        qr_widget.barWidth = qr_size
        qr_widget.barHeight = qr_size

        d = Drawing(qr_size, qr_size)
        d.add(qr_widget)

        img_buffer = io.BytesIO()
        renderPM.drawToFile(d, img_buffer, fmt='PNG', dpi=150)
        img_buffer.seek(0)

        b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    except Exception as fallback_error:
        logger.error(f"Error definitivo generando QR: {fallback_error}")
        return ""


def generar_codigo_verificacion_visual(
        codigo: str,
        incluir_barcode: bool = True,
        incluir_qr: bool = False,
        datos_qr: Optional[str] = None
) -> dict:
    """
    Genera todos los elementos visuales para el código de verificación.
    """
    resultado = {
        "codigo_texto": codigo,
        "barcode_b64": "",
        "qr_b64": "",
    }

    if incluir_barcode:
        resultado["barcode_b64"] = generar_codigo_barras_base64(codigo)

    if incluir_qr:
        datos = datos_qr or f"ISALAB|VERIFICAR|{codigo}"
        resultado["qr_b64"] = generar_qr_base64(datos)

    return resultado
