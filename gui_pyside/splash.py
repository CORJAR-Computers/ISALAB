# gui_pyside/splash.py
from PySide6.QtWidgets import QSplashScreen, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from config import BASE_DIR, QT_STYLES


class SplashScreen(QSplashScreen):
    def __init__(self):
        # Crear pixmap base
        self.pix = QPixmap(600, 300)
        self.pix.fill(QColor(QT_STYLES['secondary']))
        super().__init__(self.pix)

        # Fase 6 (G-L3): antes solo ``Qt.FramelessWindowHint``. Si durante
        # el splash aparecía otra ventana (un QMessageBox de error, una
        # actualización externa, etc.), el splash quedaba detrás y daba la
        # impresión de que la app había crasheado.
        # ``Qt.WindowStaysOnTopHint`` mantiene el splash visible encima de
        # todo hasta que se cierre explícitamente. El login aparece después
        # (``splash.finish()`` o ``splash.close()``), no compite.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.progress = 0
        self.message = "Cargando IsaLab..."
        self.logo = None
        # Fase 6 (G-L4): guard anti-reentrancy para ``setProgress``.
        # Si ``QApplication.processEvents()`` dispara un evento que a
        # su vez llama a ``setProgress`` (por ejemplo, un timer que
        # actualiza el splash), entrábamos en recursión. La flag
        # cortocircuita la segunda llamada.
        self._processing = False

        # Cargar logo si existe
        # Fase 4 (C3): el asset real es `Logo_Sidebar.png` (PascalCase).
        # La referencia lowercase fallaba en Linux/macOS.
        logo_path = BASE_DIR / "assets" / "Logo_Sidebar.png"
        if logo_path.exists():
            self.logo = QPixmap(str(logo_path))

        self._draw()

    def _draw(self):
        """Dibuja el contenido en el pixmap"""
        self.pix.fill(QColor(QT_STYLES['secondary']))
        painter = QPainter(self.pix)

        # Dibujar logo si está disponible
        if self.logo and not self.logo.isNull():
            # Escalar logo manteniendo aspecto (tamaño aproximado 200x97)
            logo_scaled = self.logo.scaled(
                200, 97, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.pix.width() - logo_scaled.width()) // 2
            y = 40  # Separación desde arriba
            painter.drawPixmap(x, y, logo_scaled)
        else:
            # Título de respaldo
            painter.setPen(Qt.white)
            font = QFont()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                self.pix.rect(),
                Qt.AlignTop | Qt.AlignHCenter,
                "IsaLab")

        # Subtítulo
        painter.setPen(Qt.white)
        font = QFont()
        font.setPointSize(12)
        font.setBold(False)
        painter.setFont(font)
        # Ajustar posición según haya logo o no
        y_sub = 150 if self.logo else 100
        painter.drawText(
            self.pix.rect().adjusted(
                0,
                y_sub,
                0,
                0),
            Qt.AlignTop | Qt.AlignHCenter,
            "Centro Diagnóstico Veterinario")

        # Mensaje de carga
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(self.pix.rect().adjusted(10, -40, 0, 0),
                         Qt.AlignBottom | Qt.AlignLeft, self.message)

        # Barra de progreso
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(QT_STYLES['primary']))
        bar_width = 500
        bar_height = 8
        bar_x = (self.pix.width() - bar_width) // 2
        bar_y = self.pix.height() - 60
        painter.drawRoundedRect(
            bar_x, bar_y, int(
                bar_width * self.progress / 100), bar_height, 4, 4)

        painter.end()
        self.setPixmap(self.pix)

    def setProgress(self, value, message=""):
        """Actualiza el progreso y mensaje, y redibuja.

        Fase 6 (G-L4): guard anti-reentrancy. ``QApplication.processEvents()``
        procesa TODOS los eventos pendientes, incluyendo timers y
        señales que podrían, a su vez, invocar ``setProgress`` otra
        vez. Sin la flag, una cascada de updates podía llevar a
        recursion profunda y stack overflow en arranques lentos
        (muchos plugins, base de datos remota, etc.).

        Con la flag, la segunda llamada (la reentrante) retorna
        inmediatamente sin procesar eventos — el ``processEvents``
        original ya está drenando la cola.
        """
        if self._processing:
            # Reentrante: no redibujamos ni procesamos eventos. El
            # ``setProgress`` que está en curso se encargará.
            return
        self._processing = True
        try:
            self.progress = min(100, max(0, value))
            if message:
                self.message = message
            self._draw()
            self.show()
            QApplication.processEvents()
        finally:
            self._processing = False
