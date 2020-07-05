from PyQt5.QtWidgets import QApplication

from drag_widget import DragWidget

def main():
    MainEventThread = QApplication([])

    MainApplication = DragWidget()

    MainApplication.show()

    return MainEventThread.exec()

if __name__ == "__main__":
    main()
