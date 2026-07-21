# main.py
import sys

# ── Fast-path: flag --version / -V ────────────────────────────────────
# Se ejecuta ANTES de importar PySide6 (que cuesta ~0.5s en cargarse) para
# que `python main.py --version` sea instantáneo y usable en scripts de CI
# / empaquetado sin penalización. Sale sin inicializar Qt, DB ni splash.
if any(arg in {'--version', '-V'} for arg in sys.argv[1:]):
    # Import tardío: config.py no depende de Qt.
    from config import __version__
    print(f"IsaLab {__version__}")
    sys.exit(0)

from pathlib import Path
import traceback
import threading
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtGui import QIcon

# Versión de la aplicación — single source of truth: ``config.__version__``.
# Se importa aquí (no en el fast-path) para que el AppUserModelID de Windows
# la use al fijar la identidad del proceso.
from config import __version__

# ── Icono en barra de tareas de Windows ──────────────────────────────
# DEBE ejecutarse ANTES de crear QApplication para que Windows
# muestre el icono correcto en la barra de tareas.
if sys.platform == 'win32':
    import ctypes
    # Establece un AppUserModelID único para esta aplicación.
    # Sin esto, Windows la agrupa bajo el icono de python.exe.
    # El número de versión va al final para que builds con versiones
    # distintas se vean como entradas separadas en la barra de tareas.
    _app_user_model_id = f"IsaLab.CentroDiagnosticoVeterinario.{__version__}"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        _app_user_model_id
    )

from config import (
    WINDOW_CONFIG,
    GLOBAL_STYLESHEET,
    PRODUCTION_MODE,
    ASSETS_DIR,
    BUNDLE_DIR,
)
from gui_pyside.splash import SplashScreen
from gui_pyside.dialogs.login_dialog import LoginDialog
from gui_pyside.dialogs.instalador_dialog import InstaladorDialog
from gui_pyside.app import LabVetApp
from utils.logger import setup_logger
from utils.security import set_current_user, clear_current_user
from database.connection import DatabaseManager
from gui_pyside.utils.messages import install_messagebox_style_filter

from icon_manager import inicializar_manager, obtener_icono

logger = setup_logger()


class ExceptionHandler(QObject):
    """Manejador centralizado de excepciones que emite señales seguras para Qt."""
    exception_raised = Signal(str, str)  # (tipo, mensaje)

    def __init__(self):
        super().__init__()
        self._original_excepthook = sys.excepthook
        self._original_thread_excepthook = None

    def install(self):
        """Instala el manejador de excepciones globally."""
        sys.excepthook = self._handle_exception

        # Manejar excepciones en threads secundarios
        if threading.current_thread() is threading.main_thread():
            self._original_thread_excepthook = threading.excepthook
            threading.excepthook = self._thread_exception_handler

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Manejador principal de excepciones no capturadas."""
        if issubclass(exc_type, KeyboardInterrupt):
            self._original_excepthook(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(
            traceback.format_exception(
                exc_type,
                exc_value,
                exc_traceback))
        logger.critical(f"Excepción no capturada: {error_msg}")

        if PRODUCTION_MODE:
            logger.error(
                f"Excepción en producción: {
                    exc_type.__name__}: {exc_value}")
            QMessageBox.critical(
                None,
                "Error del Sistema",
                f"Se produjo un error inesperado.\n\n"
                f"Por favor contacte al administrador.\n"
                f"Tipo: {exc_type.__name__}"
            )
            sys.exit(1)
        else:
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _thread_exception_handler(self, args):
        """Maneja excepciones en threads secundarios (requiere Python 3.11+)."""
        exc_type, exc_value, exc_traceback = args
        error_msg = "".join(
            traceback.format_exception(
                exc_type,
                exc_value,
                exc_traceback))
        logger.critical(f"Excepción en thread secundario: {error_msg}")

        if PRODUCTION_MODE:
            logger.error(
                f"Excepción en thread (producción): {
                    exc_type.__name__}: {exc_value}")


# Instalar el manejador global de excepciones
_exception_handler = ExceptionHandler()
_exception_handler.install()


def ocultar_info_sensible(exc_info) -> str:
    """Oculta información sensible de los stack traces en producción."""
    try:
        if PRODUCTION_MODE:
            error_type = exc_info[0].__name__ if exc_info[0] else "Error"
            error_msg = str(
                exc_info[1]) if exc_info[1] else "Error desconocido"
            logger.error(f"Error en producción: {error_type}: {error_msg}")
            return "Se produjo un error. Por favor contacte al administrador."
        else:
            return "".join(traceback.format_exception(*exc_info))
    except Exception:
        # Fallback seguro si algo falla
        return "Error inesperado. Por favor contacte al administrador."


def verificar_usuarios_existentes() -> bool:
    """Verifica si existen usuarios en el sistema."""
    try:
        db = DatabaseManager()
        row = db.fetch_one("SELECT COUNT(*) as total FROM usuarios")
        return bool(row and row['total'] > 0)
    except Exception as e:
        logger.error(f"No se pudo verificar usuarios existentes: {e}")
        return False


def verificar_salud_base_datos() -> bool:
    """Verifica que la base de datos esté accesible y operativa."""
    try:
        db = DatabaseManager()
        health = db.health_check()
        if health.get('status') != 'healthy':
            logger.error(f"Base de datos no saludable: {health}")
            return False
        logger.info(f"Health check DB: {health.get('tables', [])}")
        return True
    except Exception as e:
        logger.error(f"Error en health check de BD: {e}")
        return False


def iniciar_sesion(splash, icono_app):
    """Se ejecuta DESPUÉS de que el splash termina su animación sin congelar la app."""
    splash.close()
    splash.deleteLater()

    # Obtener instancia de app
    qt_app = QApplication.instance()

    try:
        # Debug: verificar icono antes de mostrar ventanas
        logger.info(
            f"Icono recibido en iniciar_sesion: isNull={
                icono_app.isNull()}, sizes={
                icono_app.availableSizes()}")

        if not verificar_usuarios_existentes():
            logger.info("Primera ejecución - Mostrando instalador")
            instalador = InstaladorDialog()
            instalador.setWindowIcon(icono_app)

            if instalador.exec() != QDialog.DialogCode.Accepted:
                logger.info("Instalación cancelada por el usuario")
                QMessageBox.information(
                    None, "Aviso", "La instalación fue cancelada. El sistema se cerrará.")
                qt_app.quit()
                return

        logger.info("Iniciando aplicación...")

        login_dialog = LoginDialog()
        login_dialog.setWindowIcon(icono_app)

        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            logger.info("Login cancelado")
            qt_app.quit()
            return

        usuario = getattr(login_dialog, 'usuario', {})

        # Fase 3 (issue C1 — RBAC bypass): registrar el usuario autenticado
        # en el contexto thread-local para que todos los servicios lo
        # picken automáticamente vía ``Authorizer()``. Antes, el Authorizer
        # solo se cableaba en ``UsuarioService``; el resto de servicios
        # operaban sin usuario y el RBAC estaba efectivamente burlado.
        set_current_user(usuario)
        logger.info(
            f"Usuario autenticado registrado en contexto thread-local: "
            f"{usuario.get('username', '?')} (rol: {usuario.get('rol', '?')})"
        )

        window = LabVetApp(usuario=usuario)

        # Aplicar icono a ventana principal Y a la aplicación
        window.setWindowIcon(icono_app)
        qt_app.setWindowIcon(icono_app)  # Icono en barra de tareas de Windows
        logger.info(f"Aplicando icono a ventana: isNull={icono_app.isNull()}")

        window.showMaximized()

    except Exception:
        msg = ocultar_info_sensible(sys.exc_info())
        logger.critical(f"Error fatal: {msg}")
        QMessageBox.critical(None, "Error", msg)
        qt_app.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_CONFIG['title'])
    app.setApplicationDisplayName(WINDOW_CONFIG['title'])
    app.setStyle('Fusion')
    app.setStyleSheet(GLOBAL_STYLESHEET)

    # Instalar filtro de estilos para QMessageBox
    install_messagebox_style_filter(app)

    # Verificar que la base de datos esté operativa
    if not verificar_salud_base_datos():
        QMessageBox.critical(
            None,
            "Error de Base de Datos",
            "No se puede conectar a la base de datos.\n"
            "Por favor contacte al administrador."
        )
        sys.exit(1)

    # 1. Inicializamos el gestor de iconos.
    # Usar ASSETS_DIR (no Path.cwd() ni BUNDLE_DIR) para que funcione
    # en modo congelado (.exe): el CWD del usuario puede no ser el
    # directorio del bundle. ASSETS_DIR ya apunta a BUNDLE_DIR/assets.
    # Ver issue H9 del análisis.
    inicializar_manager(ASSETS_DIR)

    # Cargar icono directamente desde archivo .ico para Windows
    ico_path = ASSETS_DIR / "icono.ico"
    if ico_path.exists():
        # QIcon puede cargar .ico directamente
        icono_app = QIcon(str(ico_path))
        if not icono_app.isNull():
            logger.info(f"Icono cargado desde {ico_path}")
        else:
            logger.warning("Icono vacío, usando fallback")
            icono_app = obtener_icono('app')
    else:
        logger.warning(f"Icono no encontrado: {ico_path}")
        icono_app = obtener_icono('app')

    app.setWindowIcon(icono_app)

    # 2. Mostrar splash
    splash = SplashScreen()
    splash.setWindowIcon(icono_app)
    splash.show()
    app.processEvents()

    # 3. ANIMACIÓN ESCALONADA (Sin usar QEventLoop bloqueante)
    QTimer.singleShot(
        500, lambda: splash.setProgress(
            30, "Cargando módulos..."))
    QTimer.singleShot(
        1000, lambda: splash.setProgress(
            60, "Inicializando interfaces..."))
    QTimer.singleShot(1500, lambda: splash.setProgress(90, "Preparando..."))
    QTimer.singleShot(1800, lambda: splash.setProgress(100, "Listo"))

    # 4. Después de 2.2 segundos, lanzamos el login de forma asíncrona
    QTimer.singleShot(2200, lambda: iniciar_sesion(splash, icono_app))

    # Configurar cierre limpio de la aplicación
    app.aboutToQuit.connect(lambda: DatabaseManager().close_all_connections())

    # Arrancamos el bucle principal de Qt. Ya no hay sys.exit() aquí.
    app.exec()


if __name__ == "__main__":
    main()
