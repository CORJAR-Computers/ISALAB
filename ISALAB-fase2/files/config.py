# config.py
"""Configuración centralizada de IsaLab"""

import os
from pathlib import Path

import sys

# Modo producción (se puede configurar con variable de entorno ISALAB_PRODUCTION_MODE)
PRODUCTION_MODE = os.getenv("ISALAB_PRODUCTION_MODE", "1") not in {"0", "false", "False"}

# Paths
if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        BUNDLE_DIR = Path(sys._MEIPASS)
    else:
        BUNDLE_DIR = Path(sys.executable).parent
    APP_DIR = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent
    APP_DIR = Path(__file__).resolve().parent

BASE_DIR = APP_DIR

# Fix Fase 2 (issue M8 complementario): permitir override de DB_PATH
# mediante variable de entorno ISALAB_DB_PATH. Útil para:
#   - Tests aislados (cada test con su DB temporal).
#   - Migraciones Alembic contra una DB específica.
#   - Despliegues donde la DB vive en otra ruta (ej. /var/lib/isalab/).
#
# Antes, DB_PATH estaba hardcoded como APP_DIR / "data" / "isalab.db"
# y no se podía override sin parchear config.py.
DB_PATH = Path(os.getenv("ISALAB_DB_PATH", str(APP_DIR / "data" / "isalab.db")))

LOG_PATH = APP_DIR / "logs" / "isalab.log"
ASSETS_DIR = BUNDLE_DIR / "assets"

# Crear directorios necesarios
DB_PATH.parent.mkdir(exist_ok=True)
LOG_PATH.parent.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Tipografía Healthcare - Figtree para mejor legibilidad clínica
FIGTREE_URL = "https://fonts.google.com/share?selection.family=Figtree:wght@300;400;500;600;700"
FONT_FAMILY = "'Segoe UI', 'Noto Sans', -apple-system, BlinkMacSystemFont, sans-serif"

# Configuración de fuente para PySide6
FONT_CONFIG = {
    'family': 'Segoe UI',
    'sizes': {
        'title': 18,
        'heading': 14,
        'body': 12,
        'small': 10,
        'mono': 11,
    },
    'weights': {
        'light': 50,
        'normal': 50,
        'bold': 75,
    }
}

# ── Sistema de Temas Light/Dark ───────────────────────────────────────
# Tema actual (se puede cambiar dinámicamente)
CURRENT_THEME = 'light'

# Paleta de temas completa
THEME_LIGHT = {
    'name': 'light',
    'primary': '#0E7490',
    'secondary': '#134E4A',
    'accent': '#15803D',
    'success': '#15803D',
    'warning': '#B45309',
    'danger': '#B91C1C',
    'gray': '#475569',
    'light_bg': '#F0FDFA',
    'dark': '#0F172A',
    'white': '#FFFFFF',
    'border': '#CBD5E1',
    'input_bg': '#FFFFFF',
    'table_alt': '#F0FDFA',
    'hover': '#E0F2FE',
    'focus_bg': '#CCFBF1',
    'header_bg': '#E0F2FE',
    'scroll_handle': '#94A3B8',
    'shadow': 'rgba(0,0,0,0.1)',
}

THEME_DARK = {
    'name': 'dark',
    'primary': '#0891B2',     # Teal más oscuro para botones en dark
    'secondary': '#0E7490',   # Cyan-700
    'accent': '#10B981',      # Emerald-500
    'success': '#10B981',
    'warning': '#F59E0B',     # Amber-500
    'danger': '#EF4444',      # Red-500
    'gray': '#94A3B8',        # Slate-400
    'light_bg': '#0F172A',    # Slate-900
    'dark': '#F1F5F9',       # Slate-100
    'white': '#1E293B',       # Slate-800 (card bg)
    'border': '#334155',     # Slate-700
    'input_bg': '#1E293B',
    'table_alt': '#1E293B',
    'hover': '#334155',
    'focus_bg': '#164E63',
    'header_bg': '#1E293B',
    'scroll_handle': '#475569',
    'shadow': 'rgba(0,0,0,0.3)',
}

# Mapping de temas para acceso rápido
THEMES = {
    'light': THEME_LIGHT,
    'dark': THEME_DARK,
}

def get_current_theme():
    """Obtiene el tema actual"""
    return THEMES[CURRENT_THEME]

def get_theme_colors():
    """Obtiene los colores del tema actual como dict plano"""
    return get_current_theme()

def set_theme(theme_name: str):
    """Cambia el tema actual"""
    global CURRENT_THEME
    if theme_name in THEMES:
        CURRENT_THEME = theme_name
        return True
    return False

def toggle_theme():
    """Alterna entre light y dark"""
    global CURRENT_THEME
    CURRENT_THEME = 'dark' if CURRENT_THEME == 'light' else 'light'
    return CURRENT_THEME

# Colores de marca IsaLab - Healthcare Professional WCAG
BRAND_COLORS = {
    'primary':   '#0E7490',   # Cyan-700 (WCAG AA)
    'secondary': '#134E4A',   # Dark Teal (WCAG AAA)
    'accent':    '#15803D',   # Green-700 (WCAG AA)
    'light':     '#E0F2FE',  # Light Teal
    'dark':      '#0F172A',   # Slate-900
    'white':     '#FFFFFF',
    'gray':      '#475569',    # Slate-600
    # Estados
    'success':   '#15803D',
    'warning':   '#B45309',
    'danger':   '#B91C1C',
    'info':     '#0E7490',
}

# CustomTkinter appearance
CTK_CONFIG = {
    'appearance_mode': 'light',   # 'light' | 'dark' | 'system'
    'color_theme':     'blue',
}

# Database
DB_CONFIG = {
    'database':          str(DB_PATH),
    'timeout':           30,
    'isolation_level':   None,
    'check_same_thread': False,
}

# UI
WINDOW_CONFIG = {
    'title':    'IsaLab - Centro Diagnóstico Veterinario',
    'geometry': '1100x700',
    'min_size': (880, 580),
    'logo':     ASSETS_DIR / 'isalab.png',
}

# Estados válidos
ESTADOS_ANIMAL  = ['Activo', 'En Tratamiento', 'Cuarentena', 'Dado de Alta']
ESTADOS_MUESTRA = ['Pendiente', 'En Proceso', 'Completado', 'Descartado']
TIPOS_MUESTRA   = ['Sangre', 'Orina', 'Heces', 'Tejido', 'Citología',
                   'Biopsia', 'Serología', 'Parasitología', 'Otro']

TIPOS_ANALISIS = {
    'Sangre':        ['Hemograma Completo', 'Química Sanguínea', 'Perfil Hepático',
                      'Perfil Renal', 'Electrolitos', 'Glucosa', 'Otros'],
    'Orina':         ['Uroanálisis', 'Proteína/Creatinina', 'Cultivo', 'Otros'],
    'Heces':         ['Coproparasitario', 'Coprocultivo', 'Sangre Oculta', 'Otros'],
    'Tejido':        ['Histopatología', 'Inmunohistoquímica', 'Otros'],
    'Citología':     ['Citología General', 'Citología Oncológica', 'Otros'],
    'Biopsia':       ['Biopsia por Aguja', 'Biopsia Excisional', 'Otros'],
    'Serología':     ['Pruebas Rápidas', 'ELISA', 'PCR', 'Otros'],
    'Parasitología': ['Detección de Parásitos', 'Cultivo de Hongos', 'Otros'],
}


# ── Módulo clínico ────────────────────────────────────────────────────────
PDF_DIR = BASE_DIR / "data" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Prefijos de código por documento  →  ISAL-0001, CONS-0001, CIRU-0001…
PREFIJOS_CODIGO = {
    'recepcion': 'ISAL',
    'consulta':  'CONS',
    'cirugia':   'CIRU',
    'vacuna':    'VAC',
}

MOTIVOS_CONSULTA = [
    'Revisión general', 'Vacunación', 'Desparasitación',
    'Control post-operatorio', 'Emergencia', 'Seguimiento',
    'Diagnóstico', 'Certificado sanitario', 'Otro',
]

TIPOS_CIRUGIA = [
    'Ovariohisterectomía', 'Orquiectomía', 'Cesárea',
    'Extracción dental', 'Laparotomía exploratoria', 'Hernia',
    'Ortopédica', 'Oftalmológica', 'Oncológica', 'Otra',
]

TIPOS_ANESTESIA = [
    'Local', 'Sedación', 'General inhalatoria',
    'General inyectable', 'Epidural', 'Combinada',
]

VACUNAS_CANINO = [
    'Moquillo-Parvo-Hepatitis (DHPPi)', 'Rabia', 'Bordetella',
    'Leptospirosis', 'Corona', 'Leishmaniasis',
]
VACUNAS_FELINO = [
    'Triple felina (FPV+FHV+FCV)', 'Rabia', 'Leucemia felina (FeLV)',
    'Inmunodeficiencia felina (FIV)', 'Peritonitis infecciosa (PIF)',
]
VACUNAS_OTRAS  = ['Rabia', 'Encefalomielitis', 'Clostridium', 'Otra']

DESPARASITANTES = [
    'Ivermectina', 'Milbemicina', 'Febendazol', 'Praziquantel',
    'Selamectina', 'Fluralaner', 'Sarolaner', 'Afoxolaner', 'Otro',
]

VACUNAS_DISPONIBLES = [
    'Rabia', 'Moquillo canino', 'Parvovirus canino', 'Hepatitis infecciosa canina',
    'Leptospirosis', 'Bordetella', 'Leucemia felina', 'Panleucopenia felina',
    'Rinotraqueitis felina', 'Calicivirus felino', 'Peritonitis infecciosa felina',
    'Polivalente canina (DHPP)', 'Polivalente felina (FVRCP)', 'Otra vacuna',
]

VIAS_ADMINISTRACION = [
    'Subcutánea (SC)', 'Intramuscular (IM)', 'Intravenosa (IV)',
    'Oral (PO)', 'Tópica', 'Intranasal', 'Otra',
]

ESTADOS_RECEPCION = ['En espera', 'En consulta', 'Finalizado', 'Cancelado']
ESTADOS_CIRUGIA   = ['Programada', 'En proceso', 'Completada', 'Cancelada']

VALIDACIONES = {
    'codigo_animal':  {'min': 3, 'max': 20,  'pattern': r'^[A-Z0-9-]+$'},
    'codigo_muestra': {'min': 3, 'max': 25,  'pattern': r'^[A-Z0-9-]+$'},
    'nombre':         {'min': 2, 'max': 100},
    'telefono':       {'pattern': r'^[\d\s\-\+\(\)]+$'},
    'email':          {'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'},
}

# QT_STYLES ahora usa get_theme_colors() dinámicamente
# para soporte de temas Light/Dark

def generate_qt_stylesheet(theme_name: str = None) -> str:
    """Genera la hoja de estilos Qt dinámicamente según el tema"""
    if theme_name is None:
        theme_name = CURRENT_THEME
    
    theme = THEMES.get(theme_name, THEMES['light'])
    
    return f"""
/* =========================================
   MESSAGEBOX - Estilos con prioridad máxima
   IMPORTANTE: Estos estilos siempre se usan independently del tema
========================================== */
QMessageBox {{
    background-color: #FFFFFF !important;
}}
QMessageBox * {{
    background-color: transparent;
}}
QMessageBox QLabel {{
    color: #0F172A !important;
    font-size: 13px;
}}
QMessageBox QPushButton {{
    background-color: #0E7490 !important;
    color: #FFFFFF !important;
    padding: 8px 24px;
    border: none !important;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    min-width: 90px;
}}
QMessageBox QPushButton:hover {{
    background-color: #134E4A !important;
}}
QMessageBox QPushButton:pressed {{
    background-color: #0F172A !important;
}}
QMessageBox QPushButton:default {{
    border: 2px solid #0E7490 !important;
}}
QDialogButtonBox QPushButton {{
    background-color: #0E7490 !important;
    color: #FFFFFF !important;
    padding: 8px 24px;
    border: none !important;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    min-width: 90px;
}}
QDialogButtonBox QPushButton:hover {{
    background-color: #134E4A !important;
}}

QMainWindow {{
    background-color: {theme['light_bg']};
    font-family: {FONT_CONFIG['family']};
}}

/* =========================================
   INPUTS Y CAMPOS DE TEXTO
========================================= */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {{
    color: {theme['dark']};
    background-color: {theme['input_bg']};
    border: 1px solid {theme['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
    border: 2px solid {theme['primary']};
    background-color: {theme['focus_bg']};
}}

QComboBox QAbstractItemView {{
    color: {theme['dark']};
    background-color: {theme['white']};
    selection-background-color: {theme['primary']};
    selection-color: white;
    border: 1px solid {theme['border']};
    border-radius: 4px;
}}

/* =========================================
   BOTONES
========================================= */
QPushButton {{
    background-color: {theme['primary']};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {theme['secondary']};
}}

QPushButton:pressed {{
    background-color: {theme['dark']};
    padding-top: 2px;
}}

/* =========================================
   TABLAS
========================================= */
QTableWidget {{
    background-color: {theme['white']};
    alternate-background-color: {theme['table_alt']};
    gridline-color: transparent;
    border: 1px solid {theme['border']};
    border-radius: 8px;
    outline: none;
}}

QHeaderView::section {{
    background-color: {theme['header_bg']};
    color: {theme['secondary']};
    padding: 12px;
    border: none;
    border-bottom: 2px solid {theme['primary']};
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
}}

QTableWidget::item:selected {{
    background-color: {theme['primary']};
    color: white;
}}

/* =========================================
   GRUPOS (QGroupBox)
========================================= */
QGroupBox {{
    font-weight: bold;
    border: 1px solid {theme['border']};
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 15px;
    background-color: {theme['white']};
    color: {theme['dark']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 4px 12px;
    color: white;
    background-color: {theme['secondary']};
    border-radius: 4px;
}}

QGroupBox QLabel {{
    color: {theme['dark']};
}}

/* =========================================
   SCROLLBARS
========================================= */
QScrollBar:vertical {{
    border: none;
    background: {theme['light_bg']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {theme['scroll_handle']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {theme['gray']};
}}

/* =========================================
   MESSAGE BOX - Estilos completos
========================================== */
QMessageBox {{
    background-color: {theme['white']};
}}

QMessageBox QLabel {{
    color: {theme['dark']};
    font-size: 13px;
}}

QMessageBox QTextBrowser {{
    color: {theme['dark']};
    background-color: {theme['light_bg']};
}}

QMessageBox #qt_msgbox_label {{
    color: {theme['dark']};
    font-size: 14px;
}}

/* =========================================
   MESSAGE BOX BUTTONS - Estilos completos
   solving gray buttons with white text on dark background
========================================== */
QMessageBox QPushButton,
QDialogButtonBox QPushButton,
QMessageBox QDialogButtonBox QPushButton {{
    background-color: {theme['primary']};
    color: #FFFFFF;
    padding: 8px 24px;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    font-size: 12px;
    min-width: 80px;
    max-width: 120px;
}}

QMessageBox QPushButton:default,
QDialogButtonBox QPushButton:default {{
    background-color: {theme['primary']};
    border: 2px solid {theme['primary']};
}}

QMessageBox QPushButton:hover,
QDialogButtonBox QPushButton:hover {{
    background-color: {theme['secondary']};
}}

QMessageBox QPushButton:pressed,
QDialogButtonBox QPushButton:pressed {{
    background-color: {theme['dark']};
}}

QMessageBox QPushButton:disabled,
QDialogButtonBox QPushButton:disabled {{
    background-color: #CBD5E1;
    color: #94A3B8;
}}

/* Secondary/alternate button style */
QMessageBox QPushButton[text="No"],
QDialogButtonBox QPushButton[text="No"] {{
    background-color: #F1F5F9;
    color: {theme['dark']};
    border: 1px solid {theme['border']};
}}

QMessageBox QPushButton[text="No"]:hover,
QDialogButtonBox QPushButton[text="No"]:hover {{
    background-color: #E2E8F0;
}}

QMessageBox QLabel {{
    color: {theme['dark']};
    font-size: 13px;
}}

QMessageBox QTextBrowser {{
    color: {theme['dark']};
    background-color: {theme['light_bg']};
}}

/* =========================================
   MESSAGE BOX BUTTONS - High Priority
========================================= */
QMessageBox QPushButton {{
    background-color: {theme['primary']} !important;
    color: white !important;
    padding: 8px 24px;
    border: 2px solid {theme['primary']} !important;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    min-width: 80px;
}}

QDialogButtonBox QPushButton {{
    background-color: {theme['primary']} !important;
    color: white !important;
    padding: 8px 24px;
    border: 2px solid {theme['primary']} !important;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    min-width: 80px;
}}

QMessageBox QPushButton:hover {{
    background-color: {theme['secondary']} !important;
    border: 2px solid {theme['secondary']} !important;
}}

QDialogButtonBox QPushButton:hover {{
    background-color: {theme['secondary']} !important;
    border: 2px solid {theme['secondary']} !important;
}}

QMessageBox QPushButton:pressed {{
    background-color: {theme['dark']} !important;
}}

QDialogButtonBox QPushButton:pressed {{
    background-color: {theme['dark']} !important;
}}

/* =========================================
   TOOLTIPS
========================================= */
QToolTip {{
    background-color: {theme['dark']};
    color: {theme['light_bg']};
    border: 1px solid {theme['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* =========================================
   LABELS
========================================= */
QLabel {{
    color: {theme['dark']};
}}

/* =========================================
   FRAMES Y CARDS
========================================= */
QFrame {{
    background-color: {theme['white']};
    color: {theme['dark']};
}}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    background-color: transparent;
}}

/* =========================================
   LISTAS
========================================= */
QListWidget {{
    background-color: {theme['white']};
    color: {theme['dark']};
    border: 1px solid {theme['border']};
    border-radius: 6px;
}}

QListWidget::item:selected {{
    background-color: {theme['primary']};
    color: white;
}}

QListWidget::item:hover {{
    background-color: {theme['hover']};
}}

/* =========================================
   RADIO BUTTONS Y CHECKBOXES
========================================= */
QRadioButton {{
    color: {theme['dark']};
}}

QRadioButton::indicator:checked {{
    background-color: {theme['primary']};
}}

QCheckBox {{
    color: {theme['dark']};
}}

QCheckBox::indicator:checked {{
    background-color: {theme['accent']};
}}

/* =========================================
   TABS
========================================= */
QTabWidget::pane {{
    border: 1px solid {theme['border']};
    border-radius: 4px;
    background-color: {theme['white']};
}}

QTabBar::tab {{
    background-color: {theme['light_bg']};
    color: {theme['gray']};
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {theme['white']};
    color: {theme['primary']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    background-color: {theme['hover']};
}}
"""


# Función convenience para obtener estilos actuales
def get_qt_stylesheet():
    """Retorna la hoja de estilos para el tema actual"""
    return generate_qt_stylesheet(CURRENT_THEME)


# Default colors para fallback (definidos antes de usar)
_default_styles = {
    'primary': '#0E7490',
    'secondary': '#134E4A',
    'accent': '#15803D',
    'success': '#15803D',
    'warning': '#B45309',
    'danger': '#B91C1C',
    'gray': '#475569',
    'light_bg': '#F0FDFA',
    'white': '#FFFFFF',
    'dark': '#0F172A',
    'border': '#CBD5E1',
}


class _QTStylesProxy:
    """Proxy dinámico para QT_STYLES - retorna colores del tema actual"""
    
    def __getitem__(self, key):
        theme = get_theme_colors()
        return theme.get(key, _default_styles.get(key, ''))
    
    def get(self, key, default=None):
        theme = get_theme_colors()
        return theme.get(key, _default_styles.get(key, default))
    
    def keys(self):
        return get_theme_colors().keys()
    
    def values(self):
        return get_theme_colors().values()
    
    def items(self):
        return get_theme_colors().items()
    
    def __iter__(self):
        return iter(get_theme_colors())
    
    def __contains__(self, key):
        return key in get_theme_colors()
    
    def __len__(self):
        return len(get_theme_colors())
    
    def __repr__(self):
        return f"QT_STYLES({CURRENT_THEME})"


# Singleton para compatibilidad hacia atrás
QT_STYLES = _QTStylesProxy()


# Alias para compatibilidad
def get_stylesheet():
    """Alias para get_qt_stylesheet()"""
    return get_qt_stylesheet()

# GLOBAL_STYLESHEET mantiene compatibilidad hacia atrás
# Se genera dinámicamente según el tema actual
GLOBAL_STYLESHEET = get_qt_stylesheet()

# ── Nuevas configuraciones para UI mejorada ───────────────────────────

# Tamaños estándar de diálogos por categoría
DIALOG_SIZES = {
    'small': (400, 300),      # Mensajes, confirmaciones
    'medium': (600, 450),     # Formularios simples
    'large': (800, 550),      # Formularios complejos (2 columnas)
    'xlarge': (1000, 650),    # Reportes, dashboards
}

# Configuración de validación visual - Healthcare WCAG
VALIDACION_VISUAL = {
    'error_color': '#B91C1C',
    'success_color': '#15803D',
    'warning_color': '#B45309',
    'transicion_ms': 200,
}

# Iconos estandarizados - versión con caracteres ASCII seguros (evita problemas de encoding)
ICONS_ASCII = {
    'save': '[SAVE]', 'cancel': '[X]', 'delete': '[DEL]', 'edit': '[EDIT]',
    'add': '[+]', 'search': '[?]', 'refresh': '[R]', 'print': '[PRINT]',
    'export': '[EXP]', 'view': '[VIEW]', 'warning': '[!]', 'success': '[OK]',
    'info': '[i]', 'loading': '...', 'login': '[LOGIN]', 'user': '[USER]',
    'password': '[KEY]', 'logout': '[OUT]', 'health': '[H]', 'lab': '[LAB]',
    'money': '$',
}

# Iconos estandarizados - versión con emojis (puede tener problemas en algunos entornos)
ICONS_EMOJI = {
    'save': '💾', 'cancel': '❌', 'delete': '🗑️', 'edit': '✏️',
    'add': '➕', 'search': '🔍', 'refresh': '🔄', 'print': '🖨️',
    'export': '📤', 'view': '👁️', 'warning': '⚠️', 'success': '✅',
    'info': 'ℹ️', 'loading': '⏳', 'login': '🔐', 'user': '👤',
    'password': '🔑', 'logout': '🚪', 'health': '🏥', 'lab': '🧪',
    'money': '💵',
}

# Usar icons ASCII por defecto en producción para evitar problemas de encoding
ICONS = ICONS_ASCII if PRODUCTION_MODE else ICONS_EMOJI

# ── Badges de estado para tablas - Healthcare Style ──────────────────
BADGE_COLORS = {
    'Pendiente': {
        'bg': '#FEF3C7',      # Amber-100
        'text': '#B45309',    # Amber-700 (WCAG)
        'border': '#B45309'
    },
    'En Proceso': {
        'bg': '#DBEAFE',      # Blue-100
        'text': '#1E40AF',    # Blue-800 (WCAG)
        'border': '#1E40AF'
    },
    'Completado': {
        'bg': '#D1FAE5',     # Emerald-100
        'text': '#065F46',    # Emerald-800 (WCAG)
        'border': '#065F46'
    },
    'Descartado': {
        'bg': '#FEE2E2',      # Red-100
        'text': '#B91C1C',    # Red-700 (WCAG)
        'border': '#B91C1C'
    },
    'Urgente': {
        'bg': '#FEE2E2',     # Red-100
        'text': '#B91C1C',   # Red-700 (WCAG)
        'border': '#B91C1C'
    },
    # Estados de animal
    'Activo': {
        'bg': '#D1FAE5',
        'text': '#065F46',
        'border': '#15803D'
    },
    'En Tratamiento': {
        'bg': '#DBEAFE',
        'text': '#1E40AF',
        'border': '#1D4ED8'
    },
    'Cuarentena': {
        'bg': '#FEE2E2',
        'text': '#B91C1C',
        'border': '#B91C1C'
    },
    'Dado de Alta': {
        'bg': '#E0E7FF',
        'text': '#3730A3',
        'border': '#4338CA'
    },
}

# Función helper para obtener estilo de badge
def get_badge_style(estado: str) -> str:
    colors = BADGE_COLORS.get(estado, BADGE_COLORS.get('Pendiente'))
    return f"""
        background-color: {colors['bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
    """