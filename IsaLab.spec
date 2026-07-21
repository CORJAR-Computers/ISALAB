# -*- mode: python ; coding: utf-8 -*-
"""
IsaLab.spec - SPEC para PyInstaller
Genera ejecutable standalone para Windows
"""

import os
from pathlib import Path

ROOT = Path(os.getcwd())
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "templates"
ALEMBIC_DIR = ROOT / "alembic"
ALEMBIC_INI = ROOT / "alembic.ini"
MANIFEST = ROOT / "isalab.manifest"

# Incluir carpetas completas con todos sus archivos.
#
# NOTA DE SEGURIDAD (issue C2):
#   NO se incluye el directorio `data/` en el bundle. Hacerlo enviaría
#   la base de datos local del desarrollador (con hashes de contraseñas
#   reales y PHI de pacientes) dentro de cada .exe distribuido.
#   El directorio `data/` se crea vacío en tiempo de ejecución mediante
#   `DatabaseManager.__init__` / `config.DB_PATH.parent.mkdir(exist_ok=True)`.
datas = [
    (str(ASSETS), "assets"),
    (str(TEMPLATES), "templates"),
    (str(ALEMBIC_DIR), "alembic"),
    (str(ALEMBIC_INI), "."),
]

# Solo los módulos de PySide6 que la app REALMENTE usa.
# NO usar collect_submodules('PySide6') — trae QtWebEngineCore y otros
# módulos opcionales que no están instalados en este entorno y rompen el build.
#
# Audit D-L6 (Fase 6):
#   * Se removieron ``PySide6.QtSvg`` y ``PySide6.QtSvgWidgets``: grep por
#     ``QtSvg`` en todo el codebase (.py) da 0 matches → eran peso muerto.
#     Si en el futuro se cargan iconos SVG vía QtSvg, volver a añadirlos.
#   * Se añadió ``icon_manager`` explícito (defensivo). PyInstaller lo
#     autodescubre desde ``main.py``, pero lo listamos para que conste en
#     el contrato del build y sobreviva a refactorings.
#   * ``services.*`` y ``orm_models.*`` NO se listan: no hay imports
#     dinámicos (verificado con ``grep -rn 'importlib\|__import__'``),
#     así que PyInstaller los descubre transitivamente desde ``main.py``.
hiddenimports = [
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtPrintSupport',
    'PySide6.QtNetwork',
    'PySide6.QtSql',
    'pyparsing',
    'pyparsing.actions',
    'pyparsing.testing',
    # Módulos propios (la mayoría autodescubiertos, listados por claridad):
    'icon_manager',
]

# Módulos que PyInstaller intenta incluir pero no necesitamos
# (evita errores de "archivo no encontrado" en módulos opcionales de Qt)
excludes = [
    'tkinter',
    'test',
    'pytest',
    'doctest',
    # Módulos Qt pesados / opcionales no utilizados por IsaLab
    'PySide6.scripts',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtWebChannel',
    'PySide6.QtWebSockets',
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.Qt3DRender',
    'PySide6.QtAsyncio',
    'PySide6.QtAxContainer',
    'PySide6.QtBluetooth',
    'PySide6.QtCanvasPainter',
    'PySide6.QtCharts',
    'PySide6.QtConcurrent',
    'PySide6.QtDBus',
    'PySide6.QtDataVisualization',
    'PySide6.QtDesigner',
    'PySide6.QtGraphs',
    'PySide6.QtGraphsWidgets',
    'PySide6.QtHelp',
    'PySide6.QtHttpServer',
    'PySide6.QtLocation',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetworkAuth',
    'PySide6.QtNfc',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtPositioning',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2',
    'PySide6.QtQuickTest',
    'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScxml',
    'PySide6.QtSensors',
    'PySide6.QtSerialBus',
    'PySide6.QtSerialPort',
    'PySide6.QtSpatialAudio',
    'PySide6.QtStateMachine',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools',
]

# ── Modo debug (issue D-L3/D-L4, Fase 6) ───────────────────────────────
# ``build_app.py --debug`` exporta ``ISALAB_DEBUG=1`` en el entorno del
# subprocess de PyInstaller. Aquí lo leemos para:
#   * ``optimize=0`` (preserva docstrings + asserts, facilita depuración).
#   * ``console=True`` (muestra stdout/stderr en una consola adjunta).
# En builds de producción (sin la env var) usamos ``optimize=2`` para
# reducir el tamaño del binario ~5-10%.
_debug = os.getenv('ISALAB_DEBUG', '0') not in {'0', 'false', 'False'}

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0 if _debug else 2,  # D-L4: 2 en producción, 0 en debug (D-L3)
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IsaLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # console=False oculta la consola en producción (correcto para UI).
    # Con ``ISALAB_DEBUG=1`` (``build_app.py --debug``) mostramos consola
    # para ver prints y tracebacks directamente en el .exe de diagnóstico.
    console=_debug,
    disable_windowed_traceback=False,
    # Icono del ejecutable (visible en el Explorador de archivos)
    icon=str(ASSETS / 'icono.ico'),
    # Manifiesto: da identidad a la app en Windows para que la barra
    # de tareas muestre el icono correcto en lugar del de python.exe
    manifest=str(MANIFEST) if MANIFEST.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    exclude_binaries=True,
    name='IsaLab',
    strip=False,
    upx=True,
    upx_exclude=[],
)