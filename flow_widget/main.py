from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel

from flow_layout import FlowLayout

class Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        flow_layout = FlowLayout()

        labels = ["Short", "Longer", "Different text", "More text", "Even longer button text"]
        for lbl in labels:
            wdgt = QLabel(lbl)
            wdgt.setStyleSheet("border: 1px solid black;")
            flow_layout.addWidget(wdgt)
        
        self.setLayout(flow_layout)

        self.setWindowTitle("Flow Layout")

def main():
    MainEventThread = QApplication([])

    MainApplication = Window()

    MainApplication.show()

    return MainEventThread.exec()

if __name__ == "__main__":
    main()
