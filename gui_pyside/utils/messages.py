"""Utilidades para mostrar mensajes consistentes en la UI."""

from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import Qt

from utils.logger import setup_logger

logger = setup_logger()

MESSAGEBOX_STYLESHEET = """
QMessageBox {
    background-color: #FFFFFF;
}
QLabel {
    color: #0F172A;
    font-size: 13px;
}
QMessageBox QPushButton {
    background-color: #0E7490;
    color: #FFFFFF;
    padding: 8px 24px;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    min-width: 90px;
    max-width: 120px;
}
QMessageBox QPushButton:hover {
    background-color: #134E4A;
}
QMessageBox QPushButton:pressed {
    background-color: #0F172A;
    padding-top: 10px;
    padding-bottom: 6px;
}
QMessageBox QPushButton:default {
    border: 2px solid #0E7490;
}
QDialogButtonBox {
    button-layout: 0;
}
"""


_messagebox_filter_installed = False


def install_messagebox_style_filter(app: Qt.QCoreApplication) -> None:
    """Instala el filtro de estilos para todos los QMessageBox"""
    global _messagebox_filter_installed
    if not _messagebox_filter_installed:
        from PySide6.QtCore import QEvent, QObject

        class MessageBoxStyleFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Show and isinstance(obj, QMessageBox):
                    obj.setStyleSheet(MESSAGEBOX_STYLESHEET)
                return super().eventFilter(obj, event)

        _filter = MessageBoxStyleFilter()
        app.installEventFilter(_filter)
        _messagebox_filter_installed = True
        logger.info("MessageBox style filter installed")


def _style_messagebox(msg_box: QMessageBox) -> None:
    """Aplica estilos consistentes al QMessageBox."""
    msg_box.setStyleSheet(MESSAGEBOX_STYLESHEET)


def show_error(
        parent: Optional[QWidget],
        user_message: str,
        error: Optional[Exception] = None) -> None:
    """Muestra un error amigable y registra el detalle técnico."""
    if error is not None:
        logger.exception(f"{user_message}: {error}")
        full_message = f"{user_message}\n{error}"
    else:
        logger.error(user_message)
        full_message = user_message

    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Error")
    msg_box.setText(full_message)
    msg_box.addButton(QMessageBox.Ok)
    _style_messagebox(msg_box)
    msg_box.exec()


def show_warning(parent: Optional[QWidget], title: str, message: str) -> None:
    """Muestra una advertencia con formato uniforme."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(QMessageBox.Ok)
    _style_messagebox(msg_box)
    msg_box.exec()


def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
    """Muestra información con formato uniforme."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(QMessageBox.Ok)
    _style_messagebox(msg_box)
    msg_box.exec()


def show_success(parent: Optional[QWidget], title: str, message: str) -> None:
    """Muestra un mensaje de éxito."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(QMessageBox.Ok)
    _style_messagebox(msg_box)
    msg_box.exec()


def confirm(parent: Optional[QWidget], title: str, message: str) -> bool:
    """Muestra un diálogo de confirmación y retorna True si el usuario acepta."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    yes_btn = msg_box.addButton("Sí", QMessageBox.YesRole)
    no_btn = msg_box.addButton("No", QMessageBox.NoRole)
    msg_box.setDefaultButton(no_btn)

    _style_messagebox(msg_box)
    msg_box.exec()

    return msg_box.clickedButton() == yes_btn
