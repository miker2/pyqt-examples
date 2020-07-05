from PyQt5.QtCore import Qt, QByteArray, QDataStream, QIODevice, QPoint, QMimeData
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPalette, QDrag

from drag_label import DragLabel

def fridgeMagnetsMimeType():
    return "application/x-fridgemagnet"

class DragWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        x, y = 5, 5
        
        with open("words.txt") as fp:
            # Read each line of the file and create a new DragLabel for it
            word = fp.readline().strip()

            while word:
                word_label = DragLabel(word, self)
                word_label.move(x, y)
                word_label.show()
                word_label.setAttribute(Qt.WA_DeleteOnClose)
                x += word_label.width() + 2
                if x >= 245:
                    x = 5
                    y += word_label.height() + 2
                # Read the next word and continue the loop.
                word = fp.readline().strip()

        new_palette = self.palette()
        new_palette.setColor(QPalette.Window, Qt.white)
        self.setPalette(new_palette)

        self.setMinimumSize(400, max(200, y))
        self.setWindowTitle("Fridge Magnets")
        self.setAcceptDrops(True)


    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(fridgeMagnetsMimeType()):
            if event.source() in self.children():
                event.setDropAction(Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()
        elif event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(fridgeMagnetsMimeType()):
            if event.source() in self.children():
                event.setDropAction(Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()
        elif event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat(fridgeMagnetsMimeType()):
            mime = event.mimeData()
            itemData = mime.data(fridgeMagnetsMimeType())
            dataStream = QDataStream(itemData, QIODevice.ReadOnly)

            dataStream.startTransaction()
            text = dataStream.readQString()
            offset = QPoint()
            dataStream >> offset

            newLabel = DragLabel(text, self)
            newLabel.move(event.pos() - offset)
            newLabel.show()
            newLabel.setAttribute(Qt.WA_DeleteOnClose)

            if event.source() == self:
                event.setDropAction(Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()

        elif event.mimeData().hasText():
            pieces = event.mimeData().text().split()
            pos = event.pos()

            for text in pieces:
                newLabel = DragLabel(text, self)
                newLabel.move(pos)
                newLabel.show()
                newLabel.setAttribute(Qt.WA_DeleteOnClose)

                pos += QPoint(newLabel.width(), 0)

            event.acceptProposedAction()

        else:
            event.ignore()

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())

        if child is None:
            return

        hotSpot = event.pos() - child.pos()

        itemData = QByteArray()
        dataStream = QDataStream(itemData, QIODevice.WriteOnly)
        dataStream.writeQString(child.labelText())
        dataStream << hotSpot

        mimeData = QMimeData()
        mimeData.setData(fridgeMagnetsMimeType(), itemData)
        mimeData.setText(child.labelText())

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(child.pixmap())
        drag.setHotSpot(hotSpot)

        child.hide()

        if drag.exec(Qt.MoveAction | Qt.CopyAction, Qt.CopyAction) == Qt.MoveAction:
            child.close()
        else:
            child.show()
