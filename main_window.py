
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import *
import sys
import batch_gui

# Example code to add batch_launcher widget into another gui.
class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)
    def write(self, text):
        self.newText.emit(str(text))

class your_main_gui(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        sys.stdout = Stream(newText=self.onUpdateText)

        self.initUI()

    def initUI(self):
        self.frame = QtWidgets.QFrame()
        self.vl = QtWidgets.QVBoxLayout()

        gui = batch_gui.BatchScanGui()

        self.vl.addWidget(gui)
        self.frame.setLayout(self.vl)
        self.setWindowTitle("main window")
        self.setCentralWidget(self.frame)

    def onUpdateText(self, text):
        cursor = self.gui.controls.message_window.textCursor()
        cursor.insertText(text)
        self.gui.controls.message_window.setTextCursor(cursor)
        self.gui.controls.message_window.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWindow = your_main_gui()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()