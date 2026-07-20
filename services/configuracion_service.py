# services/configuracion_service.py
import json
from pathlib import Path
import sys
from utils.logger import setup_logger

logger = setup_logger()

class ConfiguracionService:
    """Servicio para manejar la configuración persistente del laboratorio."""

    def __init__(self):
        # Determinar la ruta del archivo config.json en la carpeta data
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).resolve().parent.parent
            
        self.data_dir = self.base_dir / "data"
        self.config_path = self.data_dir / "lab_config.json"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def cargar_configuracion(self) -> dict:
        """Carga la configuración desde el archivo JSON. Si no existe, retorna dict vacío."""
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
