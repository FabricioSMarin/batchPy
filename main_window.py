
import batch_launcher
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import *
import sys


# Example code to add batch_launcher widget into another gui.

class your_main_gui(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.frame = QtWidgets.QFrame()
        self.vl = QtWidgets.QVBoxLayout()

        gui = batch_launcher.Launcher()

        self.vl.addWidget(gui)
        self.frame.setLayout(self.vl)
        self.setWindowTitle("main window")
        self.setCentralWidget(self.frame)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWindow = your_main_gui()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()