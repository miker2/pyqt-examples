# This Python file uses the following encoding: utf-8
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, \
    QFileDialog, QInputDialog
from PyQt5.QtCore import QSize, QDir

import pyqtgraph as pg
import json
import pathlib
from visualizer_3d_widget import VisualizerWidget


class Viz3d(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(640, 480))
        self.setWindowTitle("Viz3d example")
        self.setObjectName("Viz3d")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        self.viz_widget = VisualizerWidget(self)
        layout.addWidget(self.viz_widget)

        open_file_btn = QPushButton("Open file")
        open_file_btn.clicked.connect(self.read_file)
        layout.addWidget(open_file_btn)

        add_axis_button = QPushButton("Add axis")
        add_axis_button.clicked.connect(self.add_axis)
        layout.addWidget(add_axis_button)


    def read_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open file", QDir.homePath())

        if filename != '':
            ext = pathlib.Path(filename).suffix
            if ext.lower() == '.json':
                with open(filename, mode="r") as f:
                    data = json.load(f)
                    for e in data:
                        #print(e['board_pose'])
                        self.viz_widget.addAxis(**e['board_pose'])
            elif ext.lower() == '.stl':
                print(f"Got stl file: {filename}")
                self.viz_widget.drawMesh(filename)

    def add_axis(self):
        text, res = QInputDialog.getMultiLineText(self, "Enter axis info", "Axis info",
                                                 "enter json here")

        if res:
            print("\n\n")
            text = text.replace("'", '"')
            print(text)
            try:
                data = json.loads(text)
                print(data)
                print("\n")
                self.viz_widget.addAxis(**data)
            except JSONDecodeError:
                print(f"Entered text is invalid json:\n{text}")

if __name__ == "__main__":
    MainEventThread = QApplication([])

    MainApplication = Viz3d()
    MainApplication.show()

    MainEventThread.exec()
