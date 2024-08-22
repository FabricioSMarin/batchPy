
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QTextEdit, QCheckBox, QComboBox
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder
from ImageView import ImageView

class Controls(QWidget):
    def __init__(self):
        super(Controls, self).__init__()
        self.setupUi()

    def setupUi(self):
        size1 = 30
        size2 = 60
        size3 = 110
        size4 = 200
        size5 = 500
        height = 25
        eta_lbl = QLabel("ETA")
        eta_lbl.setFixedSize(size1,height)
        self.eta = QLabel("0")
        self.eta.setFixedSize(size4,height)

        pi_dir_lbl = QLabel("PI directory")
        pi_dir_lbl.setFixedSize(size1,height)
        self.pi_dir= QLineEdit("/")
        self.pi_dir.setFixedSize(650,height)
        pi_box = QHBoxLayout()
        # pi_box.setContentsMargins(0,10,0,0)
        pi_box.addWidget(pi_dir_lbl)
        pi_box.addWidget(self.pi_dir)
        pi_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.setup_btn = QPushButton("setup")
        self.setup_btn.setFixedSize(size2, height)
        self.begin_btn = QPushButton("Begin")
        self.begin_btn.setFixedSize(size2, height)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedSize(size2, height)
        self.continue_btn = QPushButton("Resume")
        self.continue_btn.setFixedSize(size2, height)
        self.abort_btn = QPushButton("Abort")
        self.abort_btn.setFixedSize(size2, height)

        self.visual_box = ComboBoxWithPlaceholder("view option", exclusive=True)
        options = ["trajectory preview","position stream","spectra"]
        self.visual_box.addItems(options)
        self.visual_box.setFixedWidth(size3)
        self.visual_box.check_selected([1])

        c1 = QHBoxLayout()
        c1.addWidget(eta_lbl)
        c1.addWidget(self.eta)
        c1.addWidget(self.begin_btn)
        c1.addWidget(self.pause_btn)
        c1.addWidget(self.continue_btn)
        c1.addWidget(self.abort_btn)
        c1.addWidget(self.setup_btn)
        c1.addWidget(self.visual_box)

        self.message_window = QTextEdit("")
        self.message_window.setFixedSize(700, 300)
        self.message_window.setStyleSheet("background: beige; color: black")
        self.message_window.setReadOnly(True)

        control_layout = QVBoxLayout()
        control_layout.addLayout(pi_box)
        control_layout.addLayout(c1)
        control_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        controlframe = QFrame()
        controlframe.setLayout(control_layout)
        controlframe.setContentsMargins(0,0,0,0) #left, top,right, bottom
        controlframe.setFixedWidth(700)
        combined = QVBoxLayout()
        combined.addWidget(controlframe)
        combined.addWidget(self.message_window)
        combined2 = QHBoxLayout()
        combined2.addLayout(combined)

        self.view_box = ImageView()
        self.view_box.setFixedHeight(400)
        combined2.addWidget(self.view_box)

        self.make_pretty()
        self.setLayout(combined2)

    def make_pretty(self):
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QCheckBox):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::checked {background-color: orchid;}")
            else:
                pass
        return
