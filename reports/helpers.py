# reports/helpers.py
"""
Funciones auxiliares para la generación de reportes.
"""

import base64
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


def formatear_fecha(fecha: Optional[str]) -> str:
    """Convierte '2024-04-09' en '09/04/2024' (o lo que necesites)."""
    if not fecha:
        return ""

    # ✅ FIX: Si llega un String, lo convertimos a objeto fecha
    if isinstance(fecha, str):
        try:
            # Asumimos formato YYYY-MM-DD (estándar de tu BD)
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            return fecha  # Si tiene un formato raro, lo devuelve tal cual sin explotar
    else:
        fecha_obj = fecha

    # Ahora sí podemos usar .strftime() de forma segura
    return fecha_obj.strftime("%d/%m/%Y")


def formatear_hora(fecha: datetime, formato: Optional[str] = None) -> str:
    """Formatea la hora según la configuración."""
    if formato is None:
        formato = "%I:%M %p"
    if fecha is None:
        return "—"
    return fecha.strftime(formato)


def formatear_valor_numerico(
    valor: Any,
    decimales: int = 2,
    mostrar_unidad: bool = True,
    unidad: str = ""
) -> str:
    """Formatea un valor numérico para mostrar en reporte."""
    if valor is None or valor == "":
        return "—"

    try:
        valor_float = float(valor)
        if valor_float == int(valor_float) and decimales == 0:
            resultado = str(int(valor_float))
        else:
            resultado = f"{
                valor_float:,.{decimales}f}".replace(
                ",",
                "X").replace(
                ".",
                ",").replace(
                "X",
                ".")

        if mostrar_unidad and unidad:
            resultado = f"{resultado} {unidad}"

        return resultado
    except (ValueError, TypeError):
        return str(valor)


def formatear_rango(rango_min: Any, rango_max: Any, unidad: str = "") -> str:
    """Formatea un rango de referencia como 'min - max unidad'."""
    min_str = formatear_valor_numerico(rango_min, mostrar_unidad=False)
    max_str = formatear_valor_numerico(rango_max, mostrar_unidad=False)

    if min_str == "—" and max_str == "—":
        return "—"
    elif min_str == "—":
        return f"≤ {max_str} {unidad}".strip()
    elif max_str == "—":
        return f"≥ {min_str} {unidad}".strip()
    else:
        return f"{min_str} - {max_str} {unidad}".strip()


def clasificar_valor(
    valor: Any,
    rango_min: Optional[float] = None,
    rango_max: Optional[float] = None
) -> str:
    """
    Clasifica un valor según rangos de referencia.
    Retorna: 'normal', 'bajo', 'alto', 'critico_bajo', 'critico_alto', 'sin_rango'
    """
    if valor is None:
        return "sin_rango"

    try:
        valor_float = float(valor)
    except (ValueError, TypeError):
        return "sin_rango"

    if rango_min is None and rango_max is None:
        return "sin_rango"

    if rango_min is not None and rango_max is not None:
        # Calcular porcentajes de desviación
        rango = rango_max - rango_min
        if rango == 0:
            return "normal" if valor_float == rango_min else "alto"

        desviacion_porcentaje = abs(
            valor_float - ((rango_min + rango_max) / 2)) / (rango / 2) * 100

        if valor_float < rango_min:
            return "critico_bajo" if desviacion_porcentaje > 50 else "bajo"
        elif valor_float > rango_max:
            return "critico_alto" if desviacion_porcentaje > 50 else "alto"
        else:
            return "normal"

    elif rango_min is not None:
        if valor_float < rango_min * 0.75:
            return "critico_bajo"
        elif valor_float < rango_min:
            return "bajo"
        return "normal"

    else:  # solo rango_max
        if valor_float > rango_max * 1.25:
            return "critico_alto"
        elif valor_float > rango_max:
            return "alto"
        return "normal"


def obtener_clase_css_valor(clasificacion: str) -> str:
    """Retorna la clase CSS correspondiente a la clasificación del valor."""
    mapeo = {
        "normal": "valor-normal",
        "bajo": "valor-bajo",
        "alto": "valor-alto",
        "critico_bajo": "valor-critico-bajo",
        "critico_alto": "valor-critico-alto",
        "sin_rango": "valor-sin-rango",
    }
    return mapeo.get(clasificacion, "valor-sin-rango")


def obtener_indicador_valor(clasificacion: str) -> str:
    """Retorna un indicador visual (emoji/símbolo) según la clasificación."""
    mapeo = {
        "normal": "●",
        "bajo": "▼",
        "alto": "▲",
        "critico_bajo": "▼▼",
        "critico_alto": "▲▲",
        "sin_rango": "—",
    }
    return mapeo.get(clasificacion, "—")


def generar_codigo_verificacion(longitud: int = 12) -> str:
    """
    Genera un código de verificación único para el reporte.
    Permite al cliente verificar la autenticidad del documento.
    """
    datos = f"{datetime.now().isoformat()}{secrets.token_hex(16)}"
    hash_hex = hashlib.sha256(datos.encode()).hexdigest()[:longitud].upper()
    return hash_hex


def logo_a_base64(ruta: Path, max_ancho_px: int = 300) -> str:
    """Convierte una imagen de logo a base64 para embeber en HTML."""
    return imagen_a_base64(ruta, max_ancho_px)


def imagen_a_base64(ruta: Path, max_ancho_px: int = 800) -> str:
    """Convierte cualquier imagen a base64 para embeber en HTML."""
    from pathlib import Path
    ruta = Path(ruta)
    if not ruta.exists():
        return ""

    try:
        from PIL import Image
        import io

        img = Image.open(ruta)

        # Redimensionar si es necesario
        if img.width > max_ancho_px:
            ratio = max_ancho_px / img.width
            nuevo_ancho = max_ancho_px
            nuevo_alto = int(img.height * ratio)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

        # Convertir a PNG para mantener calidad
        buffer = io.BytesIO()

        # Manejar transparencia
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
            buffer_format = 'PNG'
        else:
            img = img.convert('RGB')
            buffer_format = 'PNG'

        img.save(buffer, format=buffer_format, optimize=True)
        buffer.seek(0)

        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    except Exception:
        # Fallback sin procesamiento
        try:
            b64 = base64.b64encode(ruta.read_bytes()).decode('utf-8')
            return f"data:image/png;base64,{b64}"
        except Exception:
            return ""


def calcular_edad_anios(fecha_nacimiento: Optional[datetime]) -> Optional[str]:
    """Calcula la edad en años (y meses si es menor de 1 año)."""
    if fecha_nacimiento is None:
        return None

    # ✅ FIX: Si llega un String (ej: "2022-05-10"), lo convertimos a fecha real
    if isinstance(fecha_nacimiento, str):
        try:
            # Intenta el formato estándar de tu app (yyyy-mm-dd)
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
        except ValueError:
            return None  # Si el texto tiene un formato raro, retorna vacío sin explotar

    hoy = datetime.now()
    edad_anios = hoy.year - fecha_nacimiento.year
    edad_meses = hoy.month - fecha_nacimiento.month

    if edad_meses < 0:
        edad_anios -= 1
        edad_meses += 12

    if edad_anios < 1:
        return f"{edad_meses} mes{'es' if edad_meses != 1 else ''}"
    elif edad_anios == 1:
        return "1 año"
    else:
        return f"{edad_anios} años"


def calcular_edad_meses(fecha_nacimiento: Optional[datetime]) -> Optional[int]:
    """Calcula la edad total en meses."""
    if fecha_nacimiento is None:
        return None

    hoy = datetime.now()
    return (hoy.year - fecha_nacimiento.year) * \
        12 + (hoy.month - fecha_nacimiento.month)


def calcular_edad(fecha: datetime) -> str:
    """Alias para calcular_edad_anios (compatibilidad con otros servicios)."""
    return calcular_edad_anios(fecha) or "—"


def truncar_texto(
        texto: str,
        max_longitud: int = 50,
        sufijo: str = "...") -> str:
    """Trunca un texto si excede la longitud máxima."""
    if not texto or len(texto) <= max_longitud:
        return texto or ""
    return texto[:max_longitud - len(sufijo)] + sufijo


def safe_get(diccionario: dict, clave: str, default: Any = "—") -> Any:
    """Obtiene un valor de forma segura de un diccionario anidado."""
    if not diccionario:
        return default

    keys = clave.split(".")
    valor = diccionario

    for key in keys:
        if isinstance(valor, dict):
            valor = valor.get(key)
        else:
            return default

        if valor is None:
            return default

    return valor if valor != "" else default
