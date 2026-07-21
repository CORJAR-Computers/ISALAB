# services/report_laboratorio.py
"""Puente ORM → ReporteBase para resultados de laboratorio."""

import json
from typing import Optional, Dict, List, Any

from database.models import Muestra
from services.animal_service import AnimalService
from services.muestra_service import MuestraService
from reports import (
    generar_reporte,
    generar_por_tipo,
    formatear_fecha,
    formatear_valor_numerico,
    clasificar_valor,
    generar_codigo_verificacion,
    generar_codigo_barras_base64,
    generar_qr_base64,
    imagen_a_base64,
    calcular_edad_anios, DatosLaboratorio,
    ColoresMarca, ConfiguracionReporte, Margenes,
)
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


class ReporteLaboratorioService:
    """Genera PDFs de resultados de laboratorio (persona natural y empresa).

    Fase 3 (issue C1 — RBAC bypass):
        Toda generación de PDF requiere rol ``asistente`` o superior.
        Cualquier usuario autenticado puede generar reportes (no se
        requiere rol clínico), pero se exige autenticación para evitar
        generación anónima desde procesos externos.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.muestra_svc = MuestraService(usuario_actual)
        self.animal_svc = AnimalService(usuario_actual)
        self.lab = DatosLaboratorio()
        self.authorizer = Authorizer(usuario_actual)

    def _check_perm(self) -> None:
        self.authorizer.require_role('asistente')

    # ── API pública ──────────────────────────────────────────────────────

    def generar_pdf(
            self,
            muestra_id: int,
            resultados_estructurados: Optional[List[Dict]] = None,
            es_empresa: bool = False,
            datos_empresa: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Retorna los bytes del PDF listo para streaming / descarga."""
        self._check_perm()
        contexto = self._construir_contexto(
            muestra_id, resultados_estructurados, es_empresa, datos_empresa
        )
        tipo = "laboratorio_empresa" if es_empresa else "laboratorio"

        return generar_reporte(tipo, contexto)

    def generar_y_guardar(
        self,
        muestra_id: int,
        ruta_salida: str,
        resultados_estructurados: Optional[List[Dict]] = None,
        es_empresa: bool = False,
        datos_empresa: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Genera el PDF y lo guarda en disco. Retorna la ruta."""
        self._check_perm()
        contexto = self._construir_contexto(
            muestra_id, resultados_estructurados, es_empresa, datos_empresa
        )
        tipo = "laboratorio_empresa" if es_empresa else "laboratorio"
        return generar_por_tipo(tipo, contexto, ruta_salida)

    # ── Construcción del contexto ────────────────────────────────────────

    def _construir_contexto(
        self,
        muestra_id: int,
        resultados_externos: Optional[List[Dict]],
        es_empresa: bool,
        datos_empresa: Optional[Dict],
    ) -> Dict[str, Any]:
        muestra = self.muestra_svc.obtener_muestra(muestra_id)
        animal = self.animal_svc.obtener_animal(muestra.animal_id)

        # Procesar resultados (externos > JSON interno > texto plano)
        resultados = self._procesar_resultados(
            muestra, resultados_externos
        )

        # Clasificar cada valor para indicadores visuales
        for item in resultados:
            item["clasificacion"] = self._clasificar_item(item)

        # Agrupar por sección para el template
        secciones = self._agrupar_por_seccion(resultados)

        # Verificación
        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)

        # ✅ LOGOS INSTITUCIONALES
        import sys
        from pathlib import Path

        # Obtener el directorio base del proyecto
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dir = Path(sys._MEIPASS)
            else:
                base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent

        logo_isalab_path = base_dir / "assets" / "logos" / "isalab.png"
        logo_isalab = imagen_a_base64(
            str(logo_isalab_path)) if logo_isalab_path.exists() else ""
        if logo_isalab:
            logger.debug(
                f"Logo IsaLab cargado ({
                    len(logo_isalab)} caracteres)")
        else:
            logger.debug("Logo IsaLab no encontrado o no se pudo cargar")

        logo_empresa = ""
        if es_empresa and datos_empresa and datos_empresa.get('nombre'):
            nombre_empresa = datos_empresa['nombre']
            logger.debug(f"Buscando logo para empresa: {nombre_empresa}")

            nombre_limpio = nombre_empresa.lower().replace(
                " ",
                "_").replace(
                ".",
                "").replace(
                "c._v._",
                "").replace(
                "c_v_",
                "")
            posibles_nombres = [nombre_limpio]

            if "ruffos" in nombre_limpio:
                posibles_nombres.extend(
                    ["cv_ruffos_house", "ruffos_house", "ruffos"])
            elif "cocker" in nombre_limpio:
                posibles_nombres.extend(["cocker"])
            elif "dra_yus" in nombre_limpio or "dra yus" in nombre_limpio:
                posibles_nombres.extend(["dra_yus"])
            elif "amarena" in nombre_limpio:
                posibles_nombres.extend(["amarena"])

            for nombre_archivo in posibles_nombres:
                ruta_posible = base_dir / "assets" / \
                    "logos" / f"{nombre_archivo}.png"
                if ruta_posible.exists():
                    logo_empresa = imagen_a_base64(str(ruta_posible))
                    if logo_empresa:
                        logger.debug(
                            f"Logo empresa cargado: {nombre_archivo}.png")
                        break

            if not logo_empresa:
                logger.debug(
                    f"No se encontró logo para la empresa: {nombre_empresa}")

        contexto: Dict[str, Any] = {
            # Datos laboratorio
            "lab": self.lab,
            "colores": ColoresMarca(),
            "config": ConfiguracionReporte(),
            "margenes": Margenes(),
            "metadatos": {
                "titulo": f"Reporte de Laboratorio - {animal.nombre or 'Paciente'}",
                "autor": "IsaLab - Centro Diagnóstico Veterinario",
                "asunto": f"Muestra {muestra.codigo} - {muestra.tipo_analisis or 'Análisis General'}",
                "creador": "Sistema IsaLab v1.0"
            },
            "tipografia": {
                "titulo": "Arial, sans-serif",
                "normal": "Arial, sans-serif",
                "monospace": "Courier New, monospace"
            },
            # Paciente
            "animal": animal,
            "datos_adicionales": {
                "sexo": getattr(animal, 'sexo', None),
                "municipio": getattr(animal, 'propietario_direccion', None),
                "departamento": None,
                "mp_veterinario": None,
            },
            "edad_texto": calcular_edad_anios(animal.fecha_nacimiento),
            # Muestra
            "muestra": muestra,
            "tipo_analisis": muestra.tipo_analisis or "Análisis de Laboratorio",
            "fecha_toma": formatear_fecha(muestra.fecha_recoleccion),
            "fecha_entrega": formatear_fecha(muestra.fecha_entrega) if muestra.fecha_entrega else None,
            "tecnico": muestra.tecnico or "—",
            "veterinario_ref": muestra.veterinario_ref or "—",
            "urgente": muestra.es_urgente,
            # Resultados
            "secciones": secciones,
            "resultados_planos": resultados,
            "hay_resultados": len(resultados) > 0,
            "formatear_valor_numerico": formatear_valor_numerico,
            # Observaciones
            "observaciones": self._extraer_observaciones(muestra, resultados),
            "tecnica": self._extraer_tecnica(muestra, resultados),
            # Empresa
            "es_empresa": es_empresa,
            "empresa": datos_empresa or {},
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Logos
            "logo_isalab": logo_isalab,
            "logo_empresa": logo_empresa,
        }

        return contexto

    # ── Procesamiento de resultados ──────────────────────────────────────

    def _procesar_resultados(
        self,
        muestra: Muestra,
        resultados_externos: Optional[List[Dict]],
    ) -> List[Dict[str, Any]]:
        """
        Estrategia de resolución:
        1. Si llegan resultados_externos → usar directamente
        2. Si muestra.resultado es JSON → parsear
        3. Si muestra.resultado es texto plano → convertir a item único
        """
        # 1. Externos (lista de dicts de la GUI)
        if resultados_externos:
            return self._normalizar_items(resultados_externos)

        # 2. JSON interno
        if muestra.resultado:
            try:
                datos = json.loads(muestra.resultado)
                if isinstance(datos, list):
                    return self._normalizar_items(datos)
                elif isinstance(datos, dict):
                    if "secciones" in datos:
                        items = []
                        for sec in datos["secciones"]:
                            for it in sec.get("items", []):
                                it["seccion"] = sec["nombre"]
                                items.append(it)
                        return self._normalizar_items(items)
                    elif "items" in datos:
                        return self._normalizar_items(datos["items"])
            except (json.JSONDecodeError, TypeError):
                pass

        # 3. Texto plano → un solo bloque
        if muestra.resultado:
            return [{
                "item": muestra.tipo_analisis or "Resultado",
                "resultado": muestra.resultado,
                "unidades": "",
                "ref_texto": muestra.valor_ref or "",
                "seccion": "RESULTADO",
                "ref_min": None,
                "ref_max": None,
            }]

        return []

    def _normalizar_items(self, items: List[Dict]) -> List[Dict]:
        """Asegura que cada item tenga todas las keys esperadas."""
        normalizados = []
        for it in items:
            ref_texto = str(it.get("ref_texto", it.get("referencia", "")))
            ref_min, ref_max = self._parsear_referencia(ref_texto)

            normalizados.append({
                "item": str(it.get("item", it.get("nombre", ""))),
                "resultado": it.get("resultado", it.get("valor", "")),
                "unidades": str(it.get("unidades", "")),
                "ref_texto": ref_texto,
                "ref_min": self._a_float(it.get("ref_min")) if it.get("ref_min") else ref_min,
                "ref_max": self._a_float(it.get("ref_max")) if it.get("ref_max") else ref_max,
                "seccion": it.get("seccion", "GENERAL"),
            })
        return normalizados

    def _parsear_referencia(self, ref_str: str) -> tuple:
        """
        Parsea el texto de referencia para extraer min y max.
        Maneja formatos como: "5.0 - 10.0", "5.0 10.0", "5,0 - 10,0"
        Retorna: (ref_min, ref_max) o (None, None) si no se puede parsear
        """
        import re
        if not ref_str or not ref_str.strip():
            return None, None

        try:
            # Limpiar y normalizar
            ref_limpia = ref_str.replace('–', '-').replace(',', '.')

            # Buscar patrón "min - max" o "min max"
            patron_rango = re.compile(r'([\d.]+)\s*-\s*([\d.]+)')
            match = patron_rango.search(ref_limpia)

            if match:
                return float(match.group(1)), float(match.group(2))

            # Si no hay guión, buscar dos números separados por espacio
            partes = ref_limpia.split()
            if len(partes) >= 2:
                # Intentar convertir las dos primeras partes en números
                try:
                    num1 = float(partes[0])
                    num2 = float(partes[1])
                    return num1, num2
                except ValueError:
                    pass

            return None, None
        except Exception:
            return None, None

    def _agrupar_por_seccion(self, items: List[Dict]) -> List[Dict]:
        secciones_map: Dict[str, List[Dict]] = {}
        for it in items:
            nombre_sec = it.get("seccion", "GENERAL")
            secciones_map.setdefault(nombre_sec, []).append(it)
        return [
            {"nombre": nombre, "items": lista}
            for nombre, lista in secciones_map.items()
        ]

    def _clasificar_item(self, item: Dict) -> str:
        """Delega en clasificar_valor del helpers."""
        valor = self._a_float(item.get("resultado"))
        ref_min = item.get("ref_min")
        ref_max = item.get("ref_max")
        if valor is None or ref_min is None or ref_max is None:
            return "normal"
        return clasificar_valor(valor, ref_min, ref_max)

    def _extraer_observaciones(
        self, muestra: Muestra, resultados: List[Dict]
    ) -> List[str]:
        obs = []
        if muestra.observaciones:
            obs.append(muestra.observaciones)
        # Si el JSON tenía observaciones por sección
        if muestra.resultado:
            try:
                datos = json.loads(muestra.resultado)
                if isinstance(datos, dict) and "observaciones" in datos:
                    obs.extend(datos["observaciones"])
            except (json.JSONDecodeError, TypeError):
                pass
        return obs

    def _extraer_tecnica(
        self, muestra: Muestra, resultados: List[Dict]
    ) -> str:
        if muestra.resultado:
            try:
                datos = json.loads(muestra.resultado)
                if isinstance(datos, dict) and "tecnica" in datos:
                    return datos["tecnica"]
            except (json.JSONDecodeError, TypeError):
                pass
        return ""

    @staticmethod
    def _a_float(val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
