from PyQt5.QtWidgets import QWidget, QApplication, QStyleFactory, QMainWindow, QGridLayout, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPointF, QRectF, Qt, QLineF, QSize, QTimer, pyqtSignal

import sys
from enum import Enum

try:
    import pygame
except ModuleNotFoundError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
    import pygame


class Direction(Enum):
    Left = 0
    Right = 1
    Up = 2
    Down = 3

class GamepadHandler(QWidget):

    gamepadUpdated = pyqtSignal()
    buttonUpdated = pyqtSignal(list)

    # This properly maps the shoulder buttons to an the right axis for an xbox style controller
    JOY_AXIS_MAP = { 0 : 0,
                     1 : 1,
                     2 : 4,
                     3 : 2,
                     4 : 3,
                     5 : 5 }

    def __init__(self, update_hz=10, parent=None):
        QWidget.__init__(self, parent)
        self._update_hz = update_hz
        pygame.init()
        self._timer = QTimer()

        self.axes = []
        self.hats = []
        self.buttons = []

        if not self._findGamepad():
            print("No joystick found.")
            self._timer.timeout.connect(self._findGamepad)
            self._timer.start(1000)

    def _findGamepad(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            print(f"Found joystick: {pygame.joystick.Joystick(0).get_name()}")
            self.gamepad = pygame.joystick.Joystick(0)
            self.gamepad.init()

            self._initData()

            self._timer.stop()
            self._timer = QTimer()
            self._timer.timeout.connect(self.updateGamepad)
            self._timer.start(round(1000./self._update_hz))
            return True
        return False

    def _initData(self):
        self.axes = [[0, 0] for i in range(self.gamepad.get_numaxes())]
        self.buttons = [False]*self.gamepad.get_numbuttons()
        self.hats = [(0, 0)]*self.gamepad.get_numhats()

        print(f"axes: {self.gamepad.get_numaxes()}, "
              f"buttons: {self.gamepad.get_numbuttons()}, "
              f"hats: {self.gamepad.get_numhats()}")

    def updateGamepad(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                axis_id = self.JOY_AXIS_MAP[event.axis] // 2
                idx = self.JOY_AXIS_MAP[event.axis] % 2
                self.axes[axis_id][idx] = event.value
            elif event.type == pygame.JOYHATMOTION:
                self.hats[event.hat] = event.value
            elif event.type == pygame.JOYBUTTONDOWN:
                self.buttons[event.button] = True
            elif event.type == pygame.JOYBUTTONUP:
                self.buttons[event.button] = False
            else:
                print(event)

        self.gamepadUpdated.emit()
        self.buttonUpdated.emit(self.buttons)
        #print(self.axes, self.hats, self.buttons)

    @property
    def numButtons(self):
        return len(self.buttons)

    @property
    def numAxes(self):
        return len(self.axes)

    @property
    def numHats(self):
        return len(self.hats)

    def axis(self, idx):
        return tuple(self.axes[idx])

    def hat(self, idx):
        return self.hats[idx]

    def button(self, idx):
        return self.buttons[idx]

class LEDWidget(QWidget):
    def __init__(self, n_leds=0, parent=None):
        QWidget.__init__(self, parent)

        layout = QHBoxLayout()
        self.setLayout(layout)
        self._leds = []
        for i in range(n_leds):
            self._makeLED()

    def _makeLED(self):
        led_cnt = len(self._leds)
        lbl = QLabel(str(led_cnt+1))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumSize(QSize(20,20))
        self._leds.append(lbl)
        self.layout().addWidget(lbl)

    def updateButtons(self, state):
        if len(state) > len(self._leds):
            for i in range(len(self._leds), len(state)):
                self._makeLED()

        style = "QLabel {{ background-color: {}; border-radius: 10px; }}"
        for i, v in enumerate(state):
            if v:
                self._leds[i].setStyleSheet(style.format("red"))
            else:
                self._leds[i].setStyleSheet(style.format("green"))


class Joystick(QWidget):
    def __init__(self, gamepad=None, axis=0, parent=None):
        super(Joystick, self).__init__(parent)
        self.setMinimumSize(100, 100)
        self.moving_offset = QPointF(0, 0)
        self.grab_center = False
        self.gamepad = gamepad
        self.gamepad_axis = axis
        self.__max_distance = 50

        if self.gamepad is not None:
            self.gamepad.gamepadUpdated.connect(self.setPosition)

    def paintEvent(self, event):
        painter = QPainter(self)
        bounds = QRectF(-self.__max_distance, -self.__max_distance,
                        self.__max_distance * 2, self.__max_distance * 2).translated(self._center())
        painter.drawEllipse(bounds)
        painter.setBrush(Qt.black)
        painter.drawEllipse(self._centerEllipse())

    def _centerEllipse(self):
        if self.grab_center:
            return QRectF(-20, -20, 40, 40).translated(self.moving_offset)
        elif self.gamepad is not None:
            return QRectF(-5, -5, 10, 10).translated(self.moving_offset)
        return QRectF(-20, -20, 40, 40).translated(self._center())

    def _center(self):
        return QPointF(self.width()/2, self.height()/2)

    def _boundJoystick(self, point):
        limit_line = QLineF(self._center(), point)
        if (limit_line.length() > self.__max_distance):
            limit_line.setLength(self.__max_distance)
        return limit_line.p2()

    def joystickDirection(self):
        if not (self.grab_center or self.gamepad):
            return 0
        norm_vector = QLineF(self._center(), self.moving_offset)
        current_distance = norm_vector.length()
        angle = norm_vector.angle()

        distance = min(current_distance / self.__max_distance, 1.0)
        if 45 <= angle < 135:
            return (Direction.Up, distance)
        elif 135 <= angle < 225:
            return (Direction.Left, distance)
        elif 225 <= angle < 315:
            return (Direction.Down, distance)
        return (Direction.Right, distance)


    def mousePressEvent(self, ev):
        self.grab_center = self._centerEllipse().contains(ev.pos())
        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, event):
        self.grab_center = False
        self.moving_offset = QPointF(0, 0)
        self.update()

    def mouseMoveEvent(self, event):
        if self.grab_center:
            print("Moving")
            self.moving_offset = self._boundJoystick(event.pos())
            self.update()
        print(self.joystickDirection())

    def setPosition(self):
        if self.gamepad_axis < 3:
            point = QPointF(*self.gamepad.axis(self.gamepad_axis))
        else:
            point = QPointF(*self.gamepad.hat(self.gamepad_axis-3))

        self.moving_offset = self._boundJoystick(50*point + self._center())
        self.update()
        #print(self.joystickDirection())

if __name__ == '__main__':
    # Create main application window
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Cleanlooks"))
    main_window = QMainWindow()
    main_window.setWindowTitle('Joystick example')

    gamepad = GamepadHandler()

    # Create and set widget layout
    # Main widget container
    central_widget = QWidget()
    layout = QVBoxLayout()
    grid_layout = QGridLayout()
    central_widget.setLayout(layout)
    main_window.setCentralWidget(central_widget)

    layout.addLayout(grid_layout)
    # Create joysticks
    joystick_l = Joystick(gamepad, axis=0)
    joystick_r = Joystick(gamepad, axis=1)
    joystick_s = Joystick(gamepad, axis=2)
    joystick_h = Joystick(gamepad, axis=3)

    grid_layout.addWidget(joystick_l,0,0)
    grid_layout.addWidget(joystick_r,0,1)
    grid_layout.addWidget(joystick_s,1,0)
    grid_layout.addWidget(joystick_h,1,1)
    grid_layout.addWidget(Joystick(),2,0)

    led_widget = LEDWidget(gamepad.numButtons)
    layout.addWidget(led_widget)
    gamepad.buttonUpdated.connect(led_widget.updateButtons)

    main_window.show()

    ## Start Qt event loop unless running in interactive mode or using pyside.
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QApplication.instance().exec_()
