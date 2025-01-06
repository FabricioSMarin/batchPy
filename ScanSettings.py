import os, json
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal
from Setup import Setup

class ScanSettings(QWidget):
    settings_closed_sig = pyqtSignal()
    connect_server_sig = pyqtSignal()

    def __init__(self, parent):
        super(QWidget, self).__init__()
        self.parent = parent
        self.setObjectName("bathcscan_flysetup_vPy")
        self.setAutoFillBackground(True)
        self.settings_dict = {}
        self.var_dict = {}
        self.r=None
        self.initUI()
        self.make_pretty()

    def initUI(self):

        self.setup = Setup()
        for key in vars(self.setup):
            item = vars(self.setup)[key]
            if isinstance(item,QLineEdit):
                if isinstance(item, QLineEdit):
                    self.var_dict[item.objectName] = item
                    self.settings_dict[item.objectName] = ""
                    item.editingFinished.connect(self.settings_changed)
        self.setup.scan_generator.clicked.connect(self.scan_generator_changed)
        self.setup.qserver.clicked.connect(self.connect_server_clicked)
        wid = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(self.setup)
        wid.setLayout(layout)
        wid.setMinimumSize(300, 500)        # self.show()
        self.scan_generator_changed()
        self.setMinimumSize(300,500)

    def connect_server_clicked(self):
        #TODO urgent: connec to queue server if not already. print something saying if connected or not. 
        #pull queue from qserver, if remote queue  differs from local queue, prompt to A) clear remote queue and upload local queue or B) clear local queue and update with remote queue
        self.connect_server_sig.emit()
        pass

    def settings_changed(self):
        for key in self.settings_dict.keys():
            self.settings_dict[key] = self.var_dict[key].text()

    def openEvent(self):
        print("opening window")
        self.open_local_settings()

    def closeEvent(self, a0, QCloseEvent=None):
        print("closing window")
        self.settings_closed_sig.emit()
        self.save_local_settings()

    def make_pretty(self):
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            # elif isinstance(item,QRadioButton):
            #     item.setStyleSheet("background: white;color: black; border-radius: 4")
            else:
                pass

    def changeButton(self,button):
        if button.isChecked():
            button.setStyleSheet("background-color : lightblue")
            button.setText("True")

        else:
            button.setStyleSheet("background-color : grey")
            button.setText("False")

    def probe_pvs(self):
        #TODO: send request to server to get PV status for all those specified in this window.
        #if active, border = None
        #if not connected, border = red
        #update pv dict
        pass

    def open_local_settings(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_settings.json")
        if os.path.exists(fname) and os.path.getsize(fname):
            with open(fname, 'r') as f:
                settings = json.load(f)
                #get only settings that are in gui, anything else gets discarded 
                identicals = settings.keys() & self.settings_dict.keys()
        else:
            settings = self.settings_dict
            with open(fname, 'w') as f:
                json.dump(settings, f)

        for key in identicals:
            self.settings_dict[key] = settings[key]
            try: #incase local file has more settings that are not in gui
                self.var_dict[key].setText(self.settings_dict[key])
            except: 
                pass

    def save_local_settings(self):
        for key in self.settings_dict.keys():
            self.settings_dict[key] = self.var_dict[key].text()
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_settings.json")

        with open(fname, 'w') as f:
            json.dump(self.settings_dict, f)

    def restoresettings(self):
        settings = self.r.get("settings")
        self.settings_dict = settings
        for key in settings.keys():
            print(key)
        pass

    def scan_generator_changed(self):
        lines = [i for i in list(self.setup.__dict__) if "line_" in i]  #get vars with "line_" in name: 
        for line in lines:
            hbox = self.setup.__dict__[line]
            num_widgets = hbox.count()
            for i in range(num_widgets):
                hbox.itemAt(i).widget().setVisible(True)
        if self.setup.scan_generator.isChecked():
            self.setup.scan_generator.setText("profile move")
        else: 
            self.setup.scan_generator.setText("scan record")
