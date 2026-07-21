# gui_pyside/utils/settings.py
"""Persistent user settings via QSettings.

Stores theme, window geometry, and other user preferences across sessions.
"""

from PySide6.QtCore import QSettings, QSize, QPoint


class AppSettings:
    """Centralized access to application settings."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = QSettings("CORJAR", "IsaLab")
        return cls._instance

    @property
    def _s(self) -> QSettings:
        return self._settings

    # ── Theme ────────────────────────────────────────────────────────────

    def get_theme(self) -> str:
        """Return 'dark' or 'light' (default: 'dark')."""
        return self._s.value("theme/mode", "dark", type=str)

    def set_theme(self, mode: str) -> None:
        self._s.setValue("theme/mode", mode)

    # ── Window geometry ──────────────────────────────────────────────────

    def save_window_geometry(self, size: QSize, pos: QPoint) -> None:
        self._s.setValue("window/size", size)
        self._s.setValue("window/pos", pos)

    def load_window_geometry(self) -> tuple[QSize | None, QPoint | None]:
        size = self._s.value("window/size", None)
        pos = self._s.value("window/pos", None)
        return size, pos

    # ── Sidebar state ────────────────────────────────────────────────────

    def get_last_view(self) -> str:
        return self._s.value("sidebar/last_view", "dashboard", type=str)

    def set_last_view(self, view_name: str) -> None:
        self._s.setValue("sidebar/last_view", view_name)

    # ── Generic helpers ──────────────────────────────────────────────────

    def get(self, key: str, default=None):
        return self._s.value(key, default)

    def set(self, key: str, value) -> None:
        self._s.setValue(key, value)
