# services/configuracion_service.py
import json
from pathlib import Path
import sys
from typing import Optional
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()

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
        """Guarda la configuración en el archivo JSON."""
        # RBAC: requiere rol admin
        self.authorizer.require_role('admin')

        try:
            # Mantener configuración existente y actualizar con la nueva
            current_config = self.cargar_configuracion()
            current_config.update(config_data)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False
