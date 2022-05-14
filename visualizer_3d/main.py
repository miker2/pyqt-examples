# This Python file uses the following encoding: utf-8
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, \
    QFileDialog, QInputDialog, QComboBox, QHBoxLayout, QSlider
from PyQt5.QtCore import QSize, QDir, Qt

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

        hlayout = QHBoxLayout()

        self.joints = QComboBox()
        self.viz_widget.has_robot.connect(self.populate_joints)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-314)
        slider.setMaximum(314)
        slider.valueChanged.connect(self.setJointQ)
        hlayout.addWidget(self.joints)
        hlayout.addWidget(slider)
        layout.addLayout(hlayout)


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
            elif ext.lower() == '.stl' or ext.lower() == '.obj':
                print(f"Got stl or obj file: {filename}")
                self.viz_widget.drawMesh(filename)
            elif ext.lower() == '.urdf':
                print(f"Requested file: {filename} is a URDF file")
                self.viz_widget.drawURDF(filename)
            else:
                print(f"'{filename}' - Unknown file type!")

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

    def populate_joints(self):
        for j in self.viz_widget.getRobot().joints.keys():
            self.joints.addItem(j)

    def setJointQ(self, value):
        angle = value / 100.
        self.viz_widget.getRobot().setJointQ(self.joints.currentText(), angle)
        self.viz_widget.update()

if __name__ == "__main__":
    MainEventThread = QApplication([])

    MainApplication = Viz3d()
    MainApplication.show()

    MainEventThread.exec()
