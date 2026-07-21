# services/configuracion_service.py
import json
import os
from pathlib import Path
import sys
from typing import Optional
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Merge recursivo: ``overlay`` sobrescribe ``base`` hoja a hoja.

    Fase 6 (S-M10): antes, ``guardar_configuracion`` usaba
    ``current_config.update(config_data)`` que es un merge SHALLOW:
    cualquier valor dict anidado en ``config_data`` reemplazaba
    COMPLETAMENTE al dict correspondiente en ``current_config``,
    perdiendo las claves hermanas que el usuario no envió. Por ejemplo,
    si ``current_config`` tenía ``{"lab": {"nombre": "X", "nit": "Y"}}``
    y la GUI enviaba ``{"lab": {"nombre": "Z"}}``, el merge shallow
    dejaba ``{"lab": {"nombre": "Z"}}`` — perdiendo ``nit``.

    Con merge recursivo, el resultado es ``{"lab": {"nombre": "Z",
    "nit": "Y"}}``. Solo se sobrescriben las hojas que el overlay trae.
    """
    result = dict(base)  # shallow copy del nivel actual
    for key, val in overlay.items():
        if (key in result
                and isinstance(result[key], dict)
                and isinstance(val, dict)):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


class ConfiguracionService:
    """Servicio para manejar la configuración persistente del laboratorio.

    Fase 3 (issue C1 — RBAC bypass):
        - ``guardar_configuracion`` requiere rol ``admin`` (la
          configuración del laboratorio incluye datos sensibles como
          NIT, dirección, datos del director, etc.).
        - ``cargar_configuracion`` solo requiere usuario autenticado.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        # Determinar la ruta del archivo config.json en la carpeta data
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).resolve().parent.parent

        self.data_dir = self.base_dir / "data"
        self.config_path = self.data_dir / "lab_config.json"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.authorizer = Authorizer(usuario_actual)

    def cargar_configuracion(self) -> dict:
        """Carga la configuración desde el archivo JSON. Si no existe, retorna dict vacío."""
        # RBAC: cualquier usuario autenticado puede leer la configuración
        # (se necesita para mostrar datos del laboratorio en reportes, etc.)
        self.authorizer.require_authenticated()

        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return {}

    def guardar_configuracion(self, config_data: dict) -> bool:
        """Guarda la configuración en el archivo JSON.

        Fase 6 (S-M10):
            - Merge PROFUNDO (recursivo) en lugar de ``dict.update``
              shallow — preserva las claves hermanas en sub-dicts.
            - ``os.chmod(self.config_path, 0o600)`` tras escribir para
              restringir lectura/escritura al owner. ``lab_config.json``
              puede contener NIT, dirección del director, datos de
              contacto — información que no debe ser legible por otros
              usuarios del sistema operativo.
        """
        # RBAC: requiere rol admin
        self.authorizer.require_role('admin')

        try:
            # Mantener configuración existente y MERGEAR con la nueva
            # (deep merge — antes era shallow ``.update()``).
            current_config = self.cargar_configuracion()
            merged_config = _deep_merge(current_config, config_data)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, indent=4, ensure_ascii=False)

            # Fase 6 (S-M10): permisos 0o600 (rw-------) — solo el
            # owner puede leer/escribir. ``os.chmod`` no es portable a
            # Windows de la misma forma (Windows usa ACLs), pero en
            # Windows el modo se traduce a read-only flag (bit S_IWUSR)
            # así que al menos no rompe. En Linux/macOS cumple su
            # propósito de restringir acceso.
            try:
                os.chmod(self.config_path, 0o600)
            except OSError as chmod_err:
                # No es fatal — el archivo se escribió correctamente.
                logger.warning(
                    f"No se pudieron ajustar permisos 0600 en "
                    f"{self.config_path}: {chmod_err}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False
