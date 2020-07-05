
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont, QFontMetrics, QImage, QColor, QLinearGradient, QPainter, QPixmap
from PyQt5.QtCore import Qt, QRectF, QRect, QPoint

class DragLabel(QLabel):

    def __init__(self, text, parent):
        QLabel.__init__(self, parent=parent)

        font = QFont()

        metric = QFontMetrics(font)
        size = metric.size(Qt.TextSingleLine, text)

        image = QImage(size.width() + 12, size.height() + 12, QImage.Format_ARGB32_Premultiplied)
        image.fill(QColor(0, 0, 0, 0))

        font.setStyleStrategy(QFont.ForceOutline)

        gradient = QLinearGradient(0, 0, 0, image.height()-1)
        gradient.setColorAt(0.0, Qt.white)
        gradient.setColorAt(0.2, QColor(200, 200, 255))
        gradient.setColorAt(0.8, QColor(200, 200, 255))
        gradient.setColorAt(1.0, QColor(127, 127, 200))

        painter = QPainter()
        painter.begin(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(gradient)
        painter.drawRoundedRect(QRectF(0.5, 0.5, image.width()-1, image.height()-1),
                                25, 25, Qt.RelativeSize)
        painter.setFont(font)
        painter.setBrush(Qt.black)
        painter.drawText(QRect(QPoint(6, 6), size), Qt.AlignCenter | Qt.AlignVCenter, text)
        painter.end();

        self.setPixmap(QPixmap.fromImage(image))

        self._label_text = text

    def labelText(self):
        return self._label_text
