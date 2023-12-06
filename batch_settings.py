try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtGui import *
    from PyQt6.QtCore import pyqtSignal
except:
    print("pyqt6 not installed, trying pyqt5...")
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import pyqtSignal


from epics import *
# import batch_settings
import time
import pickle
import os
from datetime import datetime
import sys

class ScanSettings(QtWidgets.QMainWindow):
    def __init__(self, app):
        super(QtWidgets.QMainWindow, self).__init__()
        self.setObjectName("bathcscan_flysetup_vPy")
        self.setAutoFillBackground(True)
        self.app = app
        self.current_text = ""
        self.var_dict = {}
        self.fname = ""
        self.initUI()
        self.make_pretty()
        self.start_threads()

    def initUI(self):
        self.setup_window = Setup()
        # self.setup_window = batch_settings.Setup()
        self.setup_window.auto_update_pvs.clicked.connect(lambda: self.autoUpdateButton(self.setup_window.auto_update_pvs))
        for key in vars(self.setup_window):
            item = vars(self.setup_window)[key]
            if isinstance(item,QtWidgets.QLineEdit) or isinstance(item,QtWidgets.QPushButton):
                item.installEventFilter(self)
                if isinstance(item, QtWidgets.QLineEdit):
                    item.returnPressed.connect(self.line_edit_entered)
                    # item.setStyleSheet("background-color : default")
                    self.var_dict[item] = item.objectName()

        self.setup_window.config_file.clicked.connect(self.openfile)
        self.setup_window.save_config.clicked.connect(self.savefile)
        self.setup_window.scan_generator.clicked.connect(self.scan_generator_clicked)

        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.setup_window)
        wid.setLayout(layout)
        self.show()
        self.scan_generator_clicked()
        self.restoresettings()

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
    def line_edit_entered(self):
        #check which widget has focus
        for key in self.var_dict:
            if isinstance(key, QtWidgets.QLineEdit):
                focused = key.hasFocus()
                if focused:
                    proposed = key.text()
                    try:
                        print("cagetting PV, test")
                        new_val = caget(proposed, as_string=True,connection_timeout=0.05)
                        if new_val is None:
                            raise
                        self.current_text = proposed
                        key.setStyleSheet("border: none;")
                    except:
                        self.current_text = proposed
                        if proposed == "":
                            pass
                            key.setStyleSheet("border: none;")
                        else:
                            key.setStyleSheet("border: 1px solid red;")
                            print("cannot caput pv {}".format(key.objectName()))

    def start_threads(self):
        # Create new threads
        self.thread1 = myThreads(1, "countdown")
        self.thread1.countSig.connect(self.update_lcd)
        self.thread1.start()

    def eventFilter(self, source, event):   #this is to emmulate epics behavior where changes only take effect if cursor is within field.
        if event.type() == 10: # 10== Enter
            source.setFocus()
            if isinstance(source, QtWidgets.QLineEdit):
                self.current_text = source.text()
        elif event.type() == 11: # 11== Leave
            source.clearFocus()
            if isinstance(source, QtWidgets.QLineEdit):
                source.setText(self.current_text)
        return QtWidgets.QLineEdit.eventFilter(self, source, event)

    def update_lcd(self,val):
        self.setup_window.auto_update_pvs_lcd.display(str(val))
        if val == 1:
            self.caget_pvs()

    def autoUpdateButton(self,button):
        if button.isChecked():
            self.thread1.exit_flag=0
            self.thread1.start()
            button.setStyleSheet("background-color : lightblue")
            button.setText("Auto Update PVs in ...")
        else:
            self.thread1.exit_flag=1
            print("Stopping countdown")
            self.stop_thread()
            self.update_lcd("10")
            button.setStyleSheet("background-color : grey")
            button.setText("Auto Update disabled")

    def changeButton(self,button):
        if button.isChecked():
            button.setStyleSheet("background-color : lightblue")
            button.setText("True")

        else:
            button.setStyleSheet("background-color : grey")
            button.setText("False")

    def caget_pvs(self):
        pv_dict = self.get_active_pvs()
        for key in pv_dict.keys():
            pv = pv_dict[key]
            if pv != "" and pv != None:
                try:
                    value = caget(pv, as_string=True,connection_timeout=0.05,use_monitor=False)
                    print(value)
                    if value == None:
                        line = self.__dict__["setup_window"].__dict__["{}".format(key)]
                        if isinstance(line.itemAt(0).widget(),QtWidgets.QComboBox):
                            if line.itemAt(0).widget().currentText()=="None":
                                line.itemAt(1).widget().setStyleSheet("border: None;")
                            else:
                                line.itemAt(1).widget().setStyleSheet("border: 1px solid red;")
                        else:

                            line.itemAt(1).widget().setStyleSheet("border: 1px solid red;")
                    else:
                        key.setStyleSheet("border: None;")
                        pv_dict.update({key:[pv,value]})
                        if isinstance(key, QtWidgets.QLineEdit):
                            key.setText(value)
                        if isinstance(key, QtWidgets.QComboBox):
                            box_items = list(PV(pv,connection_timeout=0.05).enum_strs)
                            key.addItems(box_items)
                            key.setCurrentIndex(PV(pv,connection_timeout=0.05).value)
                        if isinstance(key,QtWidgets.QPushButton):
                            is_true = PV(pv,connection_timeout=0.05).value == 1
                            key.setChecked(is_true)
                            self.changeButton(key)

                except:
                    pass

    def get_active_pvs(self):
        pv_dict = {}
        for line in range(self.setup_window.num_lines):
            hbox = self.__dict__["setup_window"].__dict__["line_{}".format(line)]
            num_widgets = hbox.count()
            #TODO: get visible lines only

            for i in range(num_widgets):
                item = hbox.itemAt(i).widget()
                if isinstance(item, QtWidgets.QLineEdit) and line !=1:
                    if item.isVisible():
                        pv_dict["line_{}".format(line)] = item.text()

        return pv_dict

    def stop_thread(self):
        self.thread1.exit_flag=1
        self.thread1.quit()
        self.thread1.wait()


    def savefile(self):
        #open all pkl files in cwd, set "last opened" status to 0 for all except current file.
        try:
            cwd = os.path.dirname(os.path.abspath(__file__)) + "/"
            file = self.setup_window.config_file.text()
            settings = []
            for key in vars(self.setup_window):
                item = vars(self.setup_window)[key]
                if isinstance(item, QtWidgets.QLineEdit):
                    settings.append(item.text())
            save_list = ["settings", datetime.now(), settings, file, 1]

            with open(cwd + file, 'wb') as f:
                pickle.dump(save_list, f)
                f.close()
            return
        except IOError as e:
            print(e)

    def openfile(self):
        #open all pkl files in cwd, set "last opened" status to 0 for all except current file.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open .pkl", current_dir, "*.pkl")
        if file[0] == '':
            return

        with open(file[0],'rb') as f:
            contents = pickle.load(f)
            filetype = contents[0]
            last_opened = contents[1]
            settings = contents[2]
            self.fname = file[0].split("/")[-1]
            self.setup_window.config_file.setText(self.fname)
            for i, key in enumerate(self.var_dict):
                try:
                    key.setText(settings[i])
                except:
                    print("failed to set {} to {}".format(key,settings[i]))
            f.close()
        return

    def restoresettings(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        valid_files = []
        last_opened = []
        #check if files are .pkl and contain "settings" keyword.
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "settings":
                        last_opened.append(contents[1])
                        valid_files.append(file)
                    f.close()
        #if no  valid files exist, create new one.
        if len(valid_files) ==0:
            self.fname = "default_settings.pkl"
            self.setup_window.config_file.setText(self.fname)
            settings = []
            for key in self.var_dict:
                settings.append(key.text())
            with open(current_dir + self.fname, 'wb') as f:
                pickle.dump(["settings",datetime.now(),settings, self.fname, 1], f)
                f.close()

                return
        #if file does exist,
        else:
            #check which settings file is last opened, open that one.
            most_recent_file = valid_files[last_opened.index(max(last_opened))]
            with open(current_dir+most_recent_file,'rb') as f:
                contents = pickle.load(f)
                settings = contents[2]
                self.fname = most_recent_file
                self.setup_window.config_file.setText(self.fname)
                for i, key in enumerate(self.var_dict):
                    try:
                        key.setText(settings[i])
                    except IndexError:
                        print("settings list changed, ned to discard and update new settings file")
                    except:
                        print("cannot put {} in {}".format(settings[i], key))
        return


    def scan_generator_clicked(self,sender=None):
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

            self.setup_window.auto_update_pvs.setVisible(True)
            self.setup_window.auto_update_pvs_lcd.setVisible(True)
            self.setup_window.config_file_lbl.setVisible(True)
            self.setup_window.config_file.setVisible(True)
            self.setup_window.scan_generator_lbl.setVisible(True)
            self.setup_window.scan_generator.setVisible(True)
            self.setup_window.profile_move_lbl.setVisible(True)
            self.setup_window.profile_move.setVisible(True)

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
            self.setup_window.z_motor_lbl.setVisible(True)
            self.setup_window.z_motor.setVisible(True)
            self.setup_window.r_motor_lbl.setVisible(True)
            self.setup_window.r_motor.setVisible(True)
            self.setup_window.save_config_lbl.setVisible(True)
            self.setup_window.save_config.setVisible(True)

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

        pass

# class myThreads(threading.Thread,QtCore.QObject):
class myThreads(QtCore.QThread):
    countSig = pyqtSignal(int, name='countSig')
    pvSig = pyqtSignal()

    def __init__(self, threadID, name):
        QtCore.QThread.__init__(self)
        self.threadID = threadID
        self.name = name
        # self.pv_dict = pv_dict
        self.exit_flag = 0

    def run(self):
        print ("Starting " + self.name)
        if self.name == "countdown":
            self.countdown(int(10))
        print ("Exiting " + self.name)

    def countdown(self, t):
        t_original = t
        while t:
            time.sleep(1)
            t -= 1
            if t==0 and self.exit_flag==0:
                # self.pvSig.emit()       #update pvs
                t=t_original
            if self.exit_flag:
                break
            else:
                self.countSig.emit(t)   #update counter

class Setup(QtWidgets.QWidget):
    def __init__(self):
        super(Setup, self).__init__()
        self.setupUi()

    def setupUi(self):
        box = QtWidgets.QVBoxLayout()
        self.scroll_area()
        box.addWidget(self.scroll)
        self.setLayout(box)

        self.auto_update_pvs.setCheckable(True)
        self.auto_update_pvs.setStyleSheet("background-color : lightblue")
        self.auto_update_pvs.setChecked(True)

        self.scan_generator.setCheckable(True)
        self.scan_generator.setStyleSheet("background-color : grey")
        self.scan_generator.setChecked(False)
        self.scan_generator.setText("scan record")

        self.auto_update_pvs_lcd.setMaximumHeight(28)

    def scroll_area(self):
        item_dict = {} #[type(button, file, path, dropdown), descriptions[idx], choices[idx],defaults[idx]]
        item_dict["auto_update_pvs"] = [["button","lcd"], "enable/disable PV updater.", None, ""]
        item_dict["config_file"] = [["label","file"], "select config file if it exists", None, ""]
        item_dict["scan_generator"] = [["label", "button"], "scan record or profile move", None, None]
        item_dict["profile_move"] = [["label","linedit"], "profile move PV prefix", None, ""]

        item_dict["inner_before_wait"] = [["label","linedit"], "inner before wait busy record", None, ""]
        item_dict["inner_after_wait"] = [["label","linedit"], "inner after wait busy record", None, ""]
        item_dict["outer_before_wait"] = [["label","linedit"], "outer before wait busy record", None, ""]
        item_dict["outer_after_wait"] = [["label","linedit"], "outer before wait busy record", None, ""]
        item_dict["delay_calc"] = [["label","linedit"], "delay calc record PV to delay sending triggers", None, ""]
        item_dict["save_data"] = [["label","linedit"], "saveData PV, holds current filename", None, ""]
        item_dict["scan_inner"] = [["label","linedit"], "scan record inner loop", None, ""]
        item_dict["scan_outer"] = [["label","linedit"], "scan record outer loop", None, ""]
        # item_dict["ca_addr_list"] = [["label","linedit"], "Channel Access address list incase one or more IOC cannot connect to machine running batchscan.", None, ""]

        item_dict["xrf"] = [["combobox","linedit"], "xrf processor pv prefix", ["xspress3","xmap"], "xspress3"]
        item_dict["eiger"] = [["combobox","linedit"], "eiger  pv prefix", ["None","eiger"], "None"]
        item_dict["struck"] = [["combobox","linedit"], "struck pv prefix", ["None","struck"], "None"]
        item_dict["x_motor"] = [["label","linedit"], "x positioner", None, ""]
        item_dict["y_motor"] = [["label","linedit"], "y positioner", None, ""]
        item_dict["z_motor"] = [["label","linedit"], "z positioner", None, ""]
        item_dict["r_motor"] = [["label","linedit"], "r positioner", None, ""]
        item_dict["save_config"] = [["label","button"], "save config settings.", None, None]


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
                    object.clicked.connect(self.get_file)
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

    def get_file(self):
        try:
            sender = self.sender
            file = QFileDialog.getOpenFileName(self, "Open File", QtCore.QDir.currentPath())
            sender().setText(file)
        except:
            return
def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = ScanSettings(app)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()