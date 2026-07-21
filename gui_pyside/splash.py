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

        # Quitamos el flag de "siempre encima" para que el login pueda estar
        # delante
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.progress = 0
        self.message = "Cargando IsaLab..."
        self.logo = None

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
        """Actualiza el progreso y mensaje, y redibuja"""
        self.progress = min(100, max(0, value))
        if message:
            self.message = message
        self._draw()
        self.show()
        QApplication.processEvents()
