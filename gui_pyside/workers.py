# gui_pyside/workers.py
from PySide6.QtCore import QThread, Signal
from utils.logger import setup_logger

logger = setup_logger()


class PDFWorker(QThread):
    # Definimos las señales que enviarán datos de vuelta a la ventana principal
    finished = Signal(str)  # Emitirá la ruta del archivo si tiene éxito
    error = Signal(str)     # Emitirá el mensaje de error si falla

    def __init__(self, generador_func, data_object):
        super().__init__()
        # Recibimos CUALQUIER función de pdf_service y sus datos
        # correspondientes
        self.generador_func = generador_func
        self.data_object = data_object

    def run(self):
        """Este código se ejecuta en un hilo separado (no congela la UI)"""
        try:
            ruta_pdf = self.generador_func(self.data_object)
            self.finished.emit(ruta_pdf)
        except Exception as e:
            logger.exception(f"Error generando PDF en hilo de trabajo: {e}")
            self.error.emit(str(e))
