"""
icon_manager.py
Sistema centralizado de gestión de iconos para IsaLab

Uso:
    from icon_manager import IconManager

    manager = IconManager()
    icono = manager.obtener_icono()
    app.setWindowIcon(icono)
"""

from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from typing import Optional
import logging

from config import ASSETS_DIR

logger = logging.getLogger(__name__)


class IconManager:
    """
    Gestor centralizado de iconos para la aplicación IsaLab.

    Soporta múltiples formatos y proporciona fallbacks automáticos.
    """

    # Orden de preferencia para cargar iconos
    PREFERENCIAS = {
        'app': [
            'icono.ico',  # Icono principal de la app
            'isalab-icon-large-256-256x256.png',
            'isalab-icon-xl-512-512x512.png',
            'isalab-icon-256x256.png',
            'isalab-icon.png',
            'isalab-icon.ico',
            'isalab-icon.svg',
        ],
        'favicon': [
            'icono.ico',
            'isalab-icon-favicon-32-32x32.png',
            'favicon.png',
            'isalab-icon.ico',
        ],
        'splash': [
            'icono.ico',
            'isalab-icon-xl-512-512x512.png',
            'isalab-icon-large-256-256x256.png',
            'isalab-icon.png',
        ]
    }

    def __init__(self, carpeta_base: Optional[Path] = None):
        """
        Inicializa el gestor de iconos.

        Args:
            carpeta_base: Carpeta base para buscar assets (default: directorio actual)
        """
        self.carpeta_base = carpeta_base or ASSETS_DIR
        self._cache = {}  # Caché de iconos cargados

        logger.debug("IconManager inicializado con base: %s", self.carpeta_base)

    def obtener_icono(
            self,
            tipo: str = 'app',
            tamaño: Optional[int] = None) -> QIcon:
        """
        Obtiene un icono del tipo especificado.

        Args:
            tipo: 'app', 'favicon', 'splash' o 'custom'
            tamaño: Tamaño deseado en píxeles (opcional)

        Returns:
            QIcon cargado o icono vacío como fallback

        Ejemplo:
            icono_app = manager.obtener_icono('app')
            icono_pequeno = manager.obtener_icono('favicon', tamaño=32)
        """
        # Verificar caché
        cache_key = f"{tipo}_{tamaño}"
        if cache_key in self._cache:
            logger.debug("Icono %r obtenido del caché", tipo)
            return self._cache[cache_key]

        # Obtener rutas de preferencia
        preferencias = self.PREFERENCIAS.get(tipo, self.PREFERENCIAS['app'])

        icono = self._cargar_icono(preferencias)

        # Si se especifica tamaño, redimensionar
        if tamaño and not icono.isNull():
            pixmap = icono.pixmap(QSize(tamaño, tamaño))
            icono_redimensionado = QIcon(pixmap)
            self._cache[cache_key] = icono_redimensionado
            return icono_redimensionado

        # Guardar en caché
        self._cache[cache_key] = icono
        return icono

    def _cargar_icono(self, rutas_preferencia: list) -> QIcon:
        """
        Intenta cargar un icono desde una lista de rutas.

        Args:
            rutas_preferencia: Lista de rutas en orden de preferencia

        Returns:
            QIcon (vacío si ninguno funciona)
        """
        for ruta_relativa in rutas_preferencia:
            ruta_absoluta = self.carpeta_base / ruta_relativa

            if ruta_absoluta.exists():
                try:
                    icono = QIcon(str(ruta_absoluta))

                    # Validar que se cargó correctamente
                    if not icono.isNull():
                        tamaños = icono.availableSizes()
                        logger.info(
                            "✓ Icono cargado: %s (tamaños: %s)",
                            ruta_relativa, tamaños,
                        )
                        return icono
                    else:
                        logger.warning(
                            "⚠️  Archivo de icono válido pero vacío: %s",
                            ruta_relativa,
                        )

                except Exception as e:
                    logger.warning(
                        "⚠️  Error cargando %s: %s", ruta_relativa, e,
                    )
            else:
                logger.debug("No encontrado: %s", ruta_relativa)

        # Fallback: icono vacío (PySide6 mostrará uno por defecto)
        logger.warning(
            "⚠️  No se encontró ningún icono, usando valor por defecto")
        return QIcon()

    def cargar_icono_personalizado(
        self,
        ruta: Path,
        tamaño: Optional[int] = None
    ) -> QIcon:
        """
        Carga un icono desde una ruta específica.

        Args:
            ruta: Ruta al archivo de icono
            tamaño: Tamaño deseado (opcional)

        Returns:
            QIcon cargado
        """
        ruta_path = Path(ruta) if isinstance(ruta, str) else ruta

        if not ruta_path.exists():
            logger.error("Ruta no encontrada: %s", ruta_path)
            return QIcon()

        try:
            icono = QIcon(str(ruta_path))

            if icono.isNull():
                logger.error("Icono inválido: %s", ruta_path)
                return QIcon()

            if tamaño:
                pixmap = icono.pixmap(QSize(tamaño, tamaño))
                return QIcon(pixmap)

            logger.info("✓ Icono personalizado cargado: %s", ruta_path)
            return icono

        except Exception as e:
            logger.error("Error cargando icono: %s", e)
            return QIcon()

    def obtener_info(self) -> str:
        """Retorna información de los iconos disponibles."""
        info = ["=== Estado de Iconos IsaLab ===\n"]

        for tipo, rutas in self.PREFERENCIAS.items():
            info.append(f"\n{tipo.upper()}:")

            for ruta in rutas:
                ruta_absoluta = self.carpeta_base / ruta
                existe = "✓" if ruta_absoluta.exists() else "✗"
                info.append(f"  {existe} {ruta}")

        return "\n".join(info)


# Instancia global para usar en toda la app
_manager = None


def inicializar_manager(carpeta_base: Optional[Path] = None) -> IconManager:
    """Inicializa la instancia global del gestor de iconos."""
    global _manager
    _manager = IconManager(carpeta_base)
    return _manager


def obtener_manager() -> IconManager:
    """Obtiene la instancia global del gestor de iconos."""
    global _manager
    if _manager is None:
        _manager = IconManager()
    return _manager


def obtener_icono(tipo: str = 'app') -> QIcon:
    """Atajo para obtener un icono sin crear el manager."""
    return obtener_manager().obtener_icono(tipo)


# ========================
# EJEMPLO DE USO EN MAIN.PY
# ========================

# Este código solo se ejecuta si se corre directamente el archivo,
# no cuando se importa como módulo
def _ejemplo():
    from pathlib import Path
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Inicializar
    manager = IconManager(ASSETS_DIR)

    # Ver información
    logging.info(manager.obtener_info())

    # Cargar icono
    logging.info("Cargando icono...")
    icono = manager.obtener_icono('app')
    logging.info(f"¿Icono válido? {not icono.isNull()}")

    # Ejemplo con PySide6
    logging.info("--- Ejemplo PySide6 ---")
    logging.info("""
    from PySide6.QtWidgets import QApplication
    from icon_manager import inicializar_manager, obtener_icono

    def main():
        app = QApplication([])

        # Inicializar gestor de iconos
        inicializar_manager()

        # Obtener icono
        icono = obtener_icono('app')
        app.setWindowIcon(icono)

        # Crear ventana
        window = MyWindow()
        window.setWindowIcon(icono)
        window.show()

        app.exec()
    """)


if __name__ == "__main__":
    _ejemplo()
