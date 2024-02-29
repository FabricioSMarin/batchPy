
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
import pickle
import os
from datetime import datetime
import psutil
import subprocess
from queue_server import rqs
from redis import Redis
import json

class ScanSettings(QtWidgets.QWidget):
    settings_closed_sig = pyqtSignal()
    def __init__(self):
        super(QtWidgets.QWidget, self).__init__()
        self.setObjectName("bathcscan_flysetup_vPy")
        self.setAutoFillBackground(True)
        self.settings_dict = {}
        self.var_dict = {}
        self.r=None
        self.initUI()
        self.make_pretty()

    def initUI(self):
        self.setup_window = Setup()
        for key in vars(self.setup_window):
            item = vars(self.setup_window)[key]
            if isinstance(item,QtWidgets.QLineEdit):
                # item.installEventFilter(self)
                if isinstance(item, QtWidgets.QLineEdit):
                    self.var_dict[item.objectName] = item

        settings =  self.var_dict.keys()
        for setting in settings: 
            self.settings_dict[setting] = ""
       
        self.setup_window.scan_generator.clicked.connect(self.scan_generator_changed)
        self.setup_window.connect_server.clicked.connect(self.connect_server_clicked)
        self.setup_window.send_settings.clicked.connect(self.send_settings_clicked)

        wid = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.setup_window)
        wid.setLayout(layout)
        wid.setMinimumSize(300, 500)        # self.show()
        self.scan_generator_changed()
        self.open_local_settings()
        self.setMinimumSize(300,500)

    def connect_server_clicked(self):
        host = self.settings_dict["server_addr"]
        port = self.settings_dict["server_port"]
        self.r = Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)  
        try:
            if self.r.ping():
                print("connected to server")
            else:
                print("could not connect to server")
        except: 
            print("could not connect to server")
        return

    def command_detatch(self, command):
        # subprocess.call("{}python", "{}server.py".format(python_path,cwd), shell=True)
        # TODO: check if this starts and detaches from main process.
        subprocess.Popen([command], shell=True)
        return

    def command_response(self, command):
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            try:
                response = proc.communicate(timeout=1.0)
                response = response[0].decode("utf-8").split("\r")
                response = response[0] + "/"
            except subprocess.TimeoutExpired:
                proc.kill()
                response = ""
        except:
            response = ""
        return response

    def openEvent(self):
        print("opening window")
        self.open_local_settings()

    def closeEvent(self, a0, QCloseEvent=None):
        print("closing window")
        self.save_local_settings()
        # self.send_save_settings

    def make_pretty(self):
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QtWidgets.QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
                if key == "finish_time" or key == "start_time":
                    item.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    item.setFont(myFont)
            elif isinstance(item,QtWidgets.QComboBox):
                # item.setStyleSheet("background: lightyellow;border: 2px red; color: black")
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QtWidgets.QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            elif isinstance(item,QtWidgets.QRadioButton):
                item.setStyleSheet("background: white;color: black; border-radius: 4")
            else:
                pass
        return

    # def eventFilter(self, source, event):   #this is to emmulate epics behavior where changes only take effect if cursor is within field.
    #     if event.type() == 10: # 10== Enter
    #         source.setFocus()
    #         if isinstance(source, QtWidgets.QLineEdit):
    #             self.current_text = source.text()
    #     elif event.type() == 11: # 11== Leave
    #         source.clearFocus()
    #         if isinstance(source, QtWidgets.QLineEdit):
    #             source.setText(self.current_text)
    #     return QtWidgets.QLineEdit.eventFilter(self, source, event)

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

    def send_settings_clicked(self):
        try:
            self.r.set("settings", json.dumps(self.settings_dict))
        except Exception as e:
            print(e)
        return

    def send_save_settings(self):
        #TODO: send command to server to save settings .
        pass

    def open_local_settings(self):
            current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
            fname = "local_settings.pkl"
            valid_files = []
            #check if files are .pkl and contain "settings" keyword.
            for i, file in enumerate(os.listdir(current_dir)):
                if file.endswith(".pkl"):
                    with open(current_dir+file,'rb') as f:
                        contents = pickle.load(f)
                        if contents[0] == "local_settings":
                            valid_files.append(file)
                        f.close()
            #if no  valid files exist, create new one.
            if len(valid_files) ==0:
                settings = self.settings_dict

                with open(current_dir + fname, 'wb') as f:
                    pickle.dump(["local_settings",settings], f)
                    f.close()
            with open(current_dir + fname,'rb') as f:
                contents = pickle.load(f)
                settings = contents[1]
                for key in settings:
                    self.settings_dict[key] = settings[key]
                for key in self.settings_dict.keys():
                    self.var_dict[key].setText(self.settings_dict[key])
            return

    def save_local_settings(self):
        for key in self.settings_dict.keys():
            self.settings_dict[key] = self.var_dict[key].text()

        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        fname = "local_settings.pkl"
        valid_files = []
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "local_settings":
                        valid_files.append(file)
                    f.close()
        #use latest file
        fname = max(valid_files, key=os.path.getmtime)
        with open(current_dir + fname, 'wb') as f:
            pickle.dump(["local_settings",self.settings_dict], f)
            f.close()
            return


    def restoresettings(self):
        settings = self.r.get("settings")
        self.settings_dict = settings
        for key in settings.keys():
            print(key)
        pass

    def scan_generator_changed(self,sender=None):
        if sender ==None:
            checked = False
        else:
            checked = sender
        if checked:
            self.setup_window.scan_generator.setStyleSheet("background-color : grey")
            self.setup_window.scan_generator.setText("profile move")

            for line in range(self.setup_window.num_lines):
                hbox = self.__dict__["setup_window"].__dict__["line_{}".format(line)]
                num_widgets = hbox.count()
                for i in range(num_widgets):
                    hbox.itemAt(i).widget().setVisible(False)

            self.setup_window.config_file_lbl.setVisible(True)
            self.setup_window.config_file.setVisible(True)
            self.setup_window.scan_generator_lbl.setVisible(True)
            self.setup_window.scan_generator.setVisible(True)
            self.setup_window.profile_move_lbl.setVisible(True)
            self.setup_window.profile_move.setVisible(True)
            self.setup_window.trajectory_lbl.setVisible(True)
            self.setup_window.trajectory_cbbx.setVisible(True)
            self.setup_window.softgluezynq_lbl.setVisible(True)
            self.setup_window.softgluezynq.setVisible(True)

            self.setup_window.xrf_cbbx.setVisible(True)
            self.setup_window.xrf.setVisible(True)
            self.setup_window.eiger_cbbx.setVisible(True)
            self.setup_window.eiger.setVisible(True)
            self.setup_window.struck_cbbx.setVisible(True)
            self.setup_window.struck.setVisible(True)

            self.setup_window.x_motor_lbl.setVisible(True)
            self.setup_window.x_motor.setVisible(True)
            self.setup_window.y_motor_lbl.setVisible(True)
            self.setup_window.y_motor.setVisible(True)
            self.setup_window.r_motor_lbl.setVisible(True)
            self.setup_window.r_motor.setVisible(True)

        else:
            self.setup_window.scan_generator.setStyleSheet("background-color : lightblue")
            self.setup_window.scan_generator.setText("scan record")
            for line in range(self.setup_window.num_lines):
                hbox = self.__dict__["setup_window"].__dict__["line_{}".format(line)]
                num_widgets = hbox.count()
                for i in range(num_widgets):
                    hbox.itemAt(i).widget().setVisible(True)

            self.setup_window.profile_move_lbl.setVisible(False)
            self.setup_window.profile_move.setVisible(False)
            self.setup_window.trajectory_lbl.setVisible(False)
            self.setup_window.trajectory_cbbx.setVisible(False)
            self.setup_window.softgluezynq_lbl.setVisible(False)
            self.setup_window.softgluezynq.setVisible(False)

class Setup(QtWidgets.QWidget):
    def __init__(self):
        super(Setup, self).__init__()
        self.setupUi()

    def setupUi(self):
        box = QtWidgets.QVBoxLayout()
        self.scroll_area()
        box.addWidget(self.scroll)
        self.setLayout(box)

        self.scan_generator.setCheckable(True)
        self.scan_generator.setStyleSheet("background-color : grey")
        self.scan_generator.setChecked(False)
        self.scan_generator.setText("scan record")

    def scroll_area(self):
        item_dict = {} #[type(button, file, path, dropdown), descriptions[idx], choices[idx],defaults[idx]]
        item_dict["server_addr"] = [["label", "linedit"], "batch scan server host IP address", None, None]
        item_dict["server_port"] = [["label", "linedit"], "batch scan server port", None, None]
        item_dict["connect_server"] = [["label", "button"], "connect to server", None, None]
        item_dict["send_settings"] = [["label", "button"], "send settings to server", None, None]

        item_dict["scan_generator"] = [["label", "button"], "scan record or profile move", None, None]
        item_dict["profile_move"] = [["label","linedit"], "profile move PV prefix", None, ""]
        item_dict["trajectory"] = [["label","combobox"], "scan trajectory options", ["raster", "snake", "spiral", "lissajous", "custom"], "raster"]
        item_dict["softgluezynq"] = [["label","linedit"], "softgluezynq PV prefix", None, ""]

        item_dict["inner_before_wait"] = [["label","linedit"], "inner before wait busy record", None, ""]
        item_dict["inner_after_wait"] = [["label","linedit"], "inner after wait busy record", None, ""]
        item_dict["outer_before_wait"] = [["label","linedit"], "outer before wait busy record", None, ""]
        item_dict["outer_after_wait"] = [["label","linedit"], "outer before wait busy record", None, ""]
        item_dict["delay_calc"] = [["label","linedit"], "delay calc record PV to delay sending triggers", None, ""]
        item_dict["save_data"] = [["label","linedit"], "saveData PV, holds current filename", None, ""]
        item_dict["scan_inner"] = [["label","linedit"], "scan record inner loop", None, ""]
        item_dict["scan_outer"] = [["label","linedit"], "scan record outer loop", None, ""]
        item_dict["scan_inner_extra"] = [["label","linedit"], "extra scan record inner loop", None, ""]
        item_dict["scan_outer_extra"] = [["label","linedit"], "extra scan record outer loop", None, ""]

        item_dict["xrf"] = [["combobox","linedit"], "xrf processor pv prefix", ["None", "xspress3","xmap"], "xspress3"]
        item_dict["eiger"] = [["combobox","linedit"], "eiger  pv prefix", ["None","eiger"], "None"]
        item_dict["struck"] = [["combobox","linedit"], "struck pv prefix", ["None","struck"], "None"]
        item_dict["x_motor"] = [["label","linedit"], "x positioner", None, ""]
        item_dict["y_motor"] = [["label","linedit"], "y positioner", None, ""]
        item_dict["r_motor"] = [["label","linedit"], "r positioner", None, ""]

        v_box = self.create_widget(item_dict)
        v_box.setSpacing(0)
        v_box.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()  # Widget that contains the collection of Vertical Box
        self.scroll_widget.setLayout(v_box)
        self.scroll.setWidget(self.scroll_widget)
        return

    def create_widget(self, item_dict):
        widgetsizes = [240, 115, 50]
        height = 25
        v_box = QVBoxLayout()
        for i, key in enumerate(item_dict.keys()):
            widget_items = item_dict[key][0]
            attrs = item_dict[key]
            widgetsize = widgetsizes[len(widget_items) - 1]

            self.num_lines = len(item_dict)
            line_num = "line_{}".format(i)
            setattr(self, line_num, QHBoxLayout())
            line = self.__dict__[line_num]

            for widget in widget_items:
                if widget == "label":
                    name = key + "_lbl"
                    display = key.replace("_", " ")
                    setattr(self, name, QLabel(key))
                    object = self.__dict__[name]
                    object.setText(display)
                    object.setFixedWidth(widgetsize)
                    object.setToolTip(attrs[1])
                    line.addWidget(object)

                elif widget == "lcd":
                    name = key + "_lcd"
                    setattr(self, name, QtWidgets.QLCDNumber())
                    object = self.__dict__[name]
                    object.setFixedWidth(widgetsize)
                    font = QtGui.QFont()
                    font.setBold(False)
                    object.setFont(font)
                    object.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
                    object.setDigitCount(2)
                    object.setSegmentStyle(QtWidgets.QLCDNumber.SegmentStyle.Flat)
                    object.setProperty("intValue", 10)
                    line.addWidget(object)

                elif widget == "linedit":
                    setattr(self, key, QLineEdit())
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(attrs[3])
                    object.objectName = key
                    line.addWidget(object)

                elif widget == "button":
                    display = key.replace("_", " ")
                    setattr(self, key, QPushButton(key))
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(display)
                    line.addWidget(object)

                elif widget == "file":
                    setattr(self, key, QPushButton(key))
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(attrs[3])
                    line.addWidget(object)

                elif widget == "combobox":
                    name = key+"_cbbx"
                    setattr(self, name, QComboBox())
                    object = self.__dict__[name]
                    object.setFixedWidth(widgetsize)
                    object.setToolTip(attrs[1])
                    options = attrs[2]
                    default = attrs[3]
                    for option in options:
                        object.addItem(option)
                    idx = options.index(default)
                    object.setCurrentIndex(idx)
                    line.addWidget(object)

            v_box.addLayout(line)
        return v_box
