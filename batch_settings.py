try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import pyqtSignal
except:
    print("pyqt6 not installed, trying pyqt5...")
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import pyqtSignal

from epics import *
# import batch_settings
import time
import pickle
import os
from datetime import datetime

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
        self.start_threads()

    def initUI(self):
        self.setup_window = Setup()
        # self.setup_window = batch_settings.Setup()
        self.setup_window.update_btn.clicked.connect(lambda: self.autoUpdateButton(self.setup_window.update_btn))
        for key in vars(self.setup_window):
            item = vars(self.setup_window)[key]
            if isinstance(item,QtWidgets.QLineEdit) or isinstance(item,QtWidgets.QPushButton):
                item.installEventFilter(self)
                if isinstance(item, QtWidgets.QLineEdit):
                    item.returnPressed.connect(self.line_edit_entered)
                    item.setStyleSheet("background-color : default")
                    self.var_dict[item] = item.objectName()

        closeAction = QtGui.QAction(' &close', self)
        closeAction.triggered.connect(sys.exit)
        closeAction.setShortcut(' Ctrl+Q')

        openAction = QtGui.QAction(' &open config', self)
        openAction.triggered.connect(self.openfile)
        openAction.setShortcut(' Ctrl+O')

        saveAction = QtGui.QAction(' &save config', self)
        saveAction.triggered.connect(self.savefile)
        saveAction.setShortcut(' Ctrl+S')

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(closeAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)

        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.setup_window)
        wid.setLayout(layout)
        self.show()
        self.restoresettings()

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
                        key.setStyleSheet("background-color : default")
                    except:
                        self.current_text = proposed
                        if proposed == "":
                            key.setStyleSheet("background-color : default")
                        else:
                            key.setStyleSheet("border: 1px solid red;")
                            print("cannot caput pv {}".format(key.objectName()))

    def start_threads(self):
        # Create new threads
        # self.thread1 = myThreads(1, "countdown",self.pv_dict)
        self.thread1 = myThreads(1, "countdown")

        self.thread1.countSig.connect(self.update_lcd)
        # self.thread1.pvSig.connect(self.caget_pvs)
        # self.pv_dict = self.caget_pvs()
        self.thread1.start()
        print("test")

    def eventFilter(self, source, event):
        if event.type() == 10: # 10== Enter
            source.setFocus()
            if isinstance(source, QtWidgets.QLineEdit):
                self.current_text = source.text()
        elif event.type() == 11: # 11== Leave
            source.clearFocus()
            if isinstance(source, QtWidgets.QLineEdit):
                source.setText(self.current_text)
        return QtWidgets.QLineEdit.eventFilter(self, source, event)

    def button_pressed(self, button):
        #check which widget has focus
        pv = button.objectName()
        value = button.isChecked()
        try:
            # TODO: caput(pv, value)
            print("caputting PV, test")
            self.changeButton(button)
        except:
            # TODO: set button backfround to lightred
            print("cannot caput pv {}".format(button.objectName()))

    def update_lcd(self,val):
        self.setup_window.lcdNumber.display(str(val))

    def update_pv_dict(self,pv_dict):
        self.pv_dict = pv_dict

    def autoUpdateButton(self,button):
        if button.isChecked():
            self.thread1.exit_flag=0
            # self.pv_dict = self.caget_pvs()
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
        pv_dict = self.pv_dict
        for key in pv_dict.keys():
            pv = key.objectName()
            if pv == "" or pv == None:
                pv_dict.pop(key, None)
                break
            #MUST be on wired network to see PVS, idk how to change this.
            #TOOD: skip PV if caget takes more than 0.1 second to complete
            try:
                value = caget(pv, as_string=True,connection_timeout=0.05,use_monitor=False)
                if value == None:
                    key.setStyleSheet("border: 1px solid red;")
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
                print("cannot caget {}".format(pv))
        return pv_dict

    def stop_thread(self):
        self.thread1.exit_flag=1
        self.thread1.quit()
        self.thread1.wait()

    def closeEvent(self, event):
        try:
            self.thread1.exit_flag=1
            print("closing thread")
            print("autosaving settings")
            cwd = os.path.dirname(os.path.abspath(__file__))+"/"
            file = self.setup_window.config_file.text()
            settings = []
            for key in vars(self.setup_window):
                item = vars(self.setup_window)[key]
                if isinstance(item, QtWidgets.QLineEdit):
                    settings.append(item.text())
            save_list = ["settings", datetime.now(), settings, file, 1]

            with open(cwd+file, 'wb') as f:
                pickle.dump(save_list, f)
                f.close()
            return
        except IOError as e:
            print(e)

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
                    #TODO: check contents[0] for file description. if settings file, keep it. if not, then not a valid file.
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
                    except:
                        print("cannot put {} in {}".format(settings[i], key))
        return

# class myThreads(threading.Thread,QtCore.QObject):
class myThreads(QtCore.QThread):
    countSig = pyqtSignal(int, name='countSig')
    # pvSig = pyqtSignal()

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
        prefix = "2xfm:"
        scantype = "Fly"

        self.desc = QtWidgets.QLabel("Batch scan config")
        font = QtGui.QFont()
        font.setBold(True)
        self.desc.setFont(font)
        self.desc.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.config_file = QtWidgets.QLabel("config file")

        self.update_btn = QtWidgets.QPushButton("Auto Update PVs in ...")
        self.update_btn.setCheckable(True)
        self.update_btn.setStyleSheet("background-color : lightblue")
        self.update_btn.setChecked(True)
        self.lcdNumber = QtWidgets.QLCDNumber()
        font = QtGui.QFont()
        font.setBold(False)
        self.lcdNumber.setFont(font)
        self.lcdNumber.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.lcdNumber.setDigitCount(2)
        self.lcdNumber.setSegmentStyle(QtWidgets.QLCDNumber.SegmentStyle.Flat)
        self.lcdNumber.setProperty("intValue", 60)
        self.lcdNumber.setObjectName("lcdNumber")

        self.ibw_lbl = QtWidgets.QLabel("inboard before wait")
        self.iaw_lbl = QtWidgets.QLabel("inboard after wait")
        self.obw_lbl = QtWidgets.QLabel("outboard before wait")
        self.oaw_lbl = QtWidgets.QLabel("outboard after wait")
        self.xp3_lbl = QtWidgets.QLabel("xspress3")
        self.xmap_lbl = QtWidgets.QLabel("XMAP")
        self.struck_lbl = QtWidgets.QLabel("Struck")
        self.x_lbl = QtWidgets.QLabel("z motor")
        self.y_lbl = QtWidgets.QLabel("y motor")
        self.z_lbl = QtWidgets.QLabel("x motor")
        self.r_lbl = QtWidgets.QLabel("rotation motor")
        self.fscan1_lbl = QtWidgets.QLabel("Fscan1")
        self.fscanH_lbl = QtWidgets.QLabel("FscanH")
        self.delay_calc_lbl = QtWidgets.QLabel("Delay calc record")
        self.save_data_lbl = QtWidgets.QLabel("saveData PV")
        self.scan1_lbl = QtWidgets.QLabel("scan1")
        self.scan2_lbl = QtWidgets.QLabel("scan2")
        self.scanH_lbl = QtWidgets.QLabel("scanH")

        self.ibw = QtWidgets.QLineEdit("")
        self.iaw = QtWidgets.QLineEdit("")
        self.obw = QtWidgets.QLineEdit("")
        self.oaw = QtWidgets.QLineEdit("")
        self.xp3 = QtWidgets.QLineEdit("")
        self.xmap = QtWidgets.QLineEdit("")
        self.struck = QtWidgets.QLineEdit("")
        self.x = QtWidgets.QLineEdit("")
        self.y = QtWidgets.QLineEdit("")
        self.z = QtWidgets.QLineEdit("")
        self.r = QtWidgets.QLineEdit("")
        self.fscan1 = QtWidgets.QLineEdit("")
        self.fscanH = QtWidgets.QLineEdit("")
        self.delay_calc = QtWidgets.QLineEdit("")
        self.save_data = QtWidgets.QLineEdit("")
        self.scan1 = QtWidgets.QLineEdit("")
        self.scan2 = QtWidgets.QLineEdit("")
        self.scanH = QtWidgets.QLineEdit("")

        self.save_btn = QtWidgets.QPushButton("save settings")
        self.update_btn.setCheckable(True)
        self.update_btn.setStyleSheet("background-color : lightblue")

        # self.scan_type =QtWidgets.QPushButton(self.gridLayoutWidget)
        # self.scan_type.setCheckable(True)
        #
        # self.trajectory = QtWidgets.QComboBox()
        # self.trajectory.placeholderText = "trajectory"
        # self.trajectory.toolTip = "Scan trajectory"
        # self.trajectory.addItems("raster")
        # self.trajectory.addItems("snake")
        # self.trajectory.addItems("spiral")
        # self.trajectory.addItems("lissajous")

        self.column1 = QtWidgets.QVBoxLayout()
        self.column1.addWidget(self.desc)
        self.column1.addWidget(self.update_btn)
        self.column1.addWidget(self.ibw_lbl)
        self.column1.addWidget(self.iaw_lbl)
        self.column1.addWidget(self.obw_lbl)
        self.column1.addWidget(self.oaw_lbl)
        self.column1.addWidget(self.xp3_lbl)
        self.column1.addWidget(self.xmap_lbl)
        self.column1.addWidget(self.struck_lbl)
        self.column1.addWidget(self.x_lbl)
        self.column1.addWidget(self.y_lbl)
        self.column1.addWidget(self.z_lbl)
        self.column1.addWidget(self.r_lbl)
        self.column1.addWidget(self.fscan1_lbl)
        self.column1.addWidget(self.fscanH_lbl)
        self.column1.addWidget(self.delay_calc_lbl)
        self.column1.addWidget(self.save_data_lbl)
        self.column1.addWidget(self.scan1_lbl)
        self.column1.addWidget(self.scan2_lbl)
        self.column1.addWidget(self.scanH_lbl)

        self.column2 = QtWidgets.QVBoxLayout()
        self.column2.addWidget(self.config_file)
        self.column2.addWidget(self.lcdNumber)
        self.column2.addWidget(self.ibw)
        self.column2.addWidget(self.iaw)
        self.column2.addWidget(self.obw)
        self.column2.addWidget(self.oaw)
        self.column2.addWidget(self.xp3)
        self.column2.addWidget(self.xmap)
        self.column2.addWidget(self.struck)
        self.column2.addWidget(self.x)
        self.column2.addWidget(self.y)
        self.column2.addWidget(self.z)
        self.column2.addWidget(self.r)
        self.column2.addWidget(self.fscan1)
        self.column2.addWidget(self.fscanH)
        self.column2.addWidget(self.delay_calc)
        self.column2.addWidget(self.save_data)
        self.column2.addWidget(self.scan1)
        self.column2.addWidget(self.scan2)
        self.column2.addWidget(self.scanH)

        row = QtWidgets.QHBoxLayout()
        row.addLayout(self.column1)
        row.addLayout(self.column2)

        self.setLayout(row)

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = ScanSettings(app)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()