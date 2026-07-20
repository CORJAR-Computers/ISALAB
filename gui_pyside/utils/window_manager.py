# gui_pyside/utils/window_manager.py
"""
Gestor centralizado de ventanas para evitar que los diálogos queden atrapados
o bloqueados unos dentro de otros.
"""

from PySide6.QtWidgets import QMainWindow, QDialog
from PySide6.QtCore import QObject


class WindowManager(QObject):
    """
    Singleton que gestiona la apertura y cierre de diálogos.
    Asegura que solo haya un diálogo modal activo a la vez y que
    las ventanas no queden atrapadas.
    """
    _instance = None
    _dialog_stack = []
    _main_window = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_main_window(cls, window: QMainWindow):
        """Establece la ventana principal de la aplicación"""
        cls._main_window = window

    @classmethod
    def get_main_window(cls):
        """Obtiene la ventana principal"""
        return cls._main_window

    @classmethod
    def open_dialog(cls, dialog: QDialog, parent=None):
        """
        Abre un diálogo de manera segura, asegurando que:
        1. Se establece el padre correcto (ventana principal si no hay padre)
        2. No quede atrapado dentro de otro diálogo
        3. Se centre correctamente
        """
        # Si no tiene padre, usar la ventana principal
        if parent is None:
            parent = cls._main_window

        # Si el padre es un QWidget dentro de otro diálogo, buscar el diálogo
        # padre
        while parent and isinstance(parent, QDialog):
            parent = parent.parent()

        # Si después de buscar no hay padre, usar la ventana principal
        if parent is None:
            parent = cls._main_window

        # Establecer el padre
        dialog.setParent(parent)

        # Apilar el diálogo
        cls._dialog_stack.append(dialog)

        # Ejecutar
        result = dialog.exec()

        # Desapilar cuando termine
        if dialog in cls._dialog_stack:
            cls._dialog_stack.remove(dialog)

        return result

    @classmethod
    def close_all_dialogs(cls):
        """Cierra todos los diálogos abiertos"""
        while cls._dialog_stack:
            dialog = cls._dialog_stack.pop()
            if dialog:
                dialog.reject()

    @classmethod
    def get_active_dialog(cls):
        """Obtiene el diálogo actualmente activo"""
        return cls._dialog_stack[-1] if cls._dialog_stack else None

    @classmethod
    def is_dialog_open(cls):
        """Verifica si hay algún diálogo abierto"""
        return len(cls._dialog_stack) > 0
