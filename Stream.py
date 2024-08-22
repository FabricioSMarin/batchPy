from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal


class Stream(QtCore.QObject):
    newText = pyqtSignal(str)
    
    def write(self, text):
        self.newText.emit(str(text))