

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
import csv
import numpy as np
import pyqtgraph
from pyqtgraph import PlotWidget, plot
import os
import pickle
from datetime import datetime, timedelta
import subprocess

#GUI structure:
#   Header()  
#   Lines()
#   Controls()
#   ImageView()


#TODO: set the motor minimum velocity to 0.01 for longer dwell times.
#TODO: current scan line background (yellow) dissappears if any of the text fields are modified.
#TODO: FIX global ETA
#TODO: zero dwell time turns red even if line is set to skip.
#TODO: save message gets written even if scan was skipped.
#TODO: set line background to light gray if line set to normal
#TODO: dynamically adjust font size to fit inside box

class BatchScanGui(QtWidgets.QMainWindow):
    def __init__(self,app):
        super(QtWidgets.QMainWindow, self).__init__()
        self.app = app
        self.view1 = 1100
        self.view2 = 1600
        self.view3 = 1330
        self.view4 = 1830
        self.active_line = -1
        self.session_file = "default_session.pkl"
        self.setWindowTitle("Batch Py V1.0.0")

        self.update_interval = 10
        self.num_lines = 40
        self.show_lines = 5
        self.line_names = []
        for i in range(self.num_lines): #max number of lines
            self.line_names.append("line_{}".format(str(i)))
        for v in self.line_names:
            setattr(self, v, Line())
        self.initUI()
        self.restore_session()
        # self.setFixedWidth(self.view1)
        self.show()

    def initUI(self):
        self.header = Header()
        self.controls = Controls()

        lineframe = QtWidgets.QFrame()
        tmp_layout = QtWidgets.QVBoxLayout()
        for i in range(self.num_lines):
            line = self.__dict__[self.line_names[i]]
            line.objectName = str(i)
            line.setAutoFillBackground(True)
            tmp_layout.addWidget(line)

        lineframe.setLayout(tmp_layout)
        lineframe.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);border-width: 1;border-radius: 3;border-style: solid;border-color: rgb(10, 10, 10)}")
        lineframe.setContentsMargins(0,0,0,0) #left, top,right, bottom

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(lineframe)
        layout.addWidget(self.controls)
        layout.setSpacing(0)
        layout.setContentsMargins(10,5,10,10) #left, top,right, bottom
        # layout.setContentsMargins(0,0,0,0) #left, top,right, bottom

        self.wid = QtWidgets.QWidget()
        self.setCentralWidget(self.wid)
        self.wid.setLayout(layout)
        self.wid.setStyleSheet("background: white")
        self.line_0.current_line.setChecked(True)
        self.closeAction = QAction(' &close', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        self.initRecordAction = QAction(" &init scan record", self)
        self.initPVsAction = QAction(" init PVs ", self)
        self.openAction = QAction(' &open PV config', self)
        self.openAction.setShortcut(' Ctrl+O')
        self.saveAction = QAction(' &save session', self)
        self.saveAction.setShortcut(' Ctrl+S')
        self.exportScanParamsAction = QAction(' &export scan parameters', self)
        self.exportScanParamsAction.triggered.connect(self.export_scan_params)
        self.importScanParamsAction = QAction(' &import scan parameters', self)
        self.importScanParamsAction.triggered.connect(self.import_scan_params)

        self.tomoAction = QAction(' tomo view', self, checkable=True)
        self.tomoAction.triggered.connect(self.view_changed)
        self.miscviewAction = QAction(' misc view', self, checkable=True)
        self.miscviewAction.triggered.connect(self.view_changed)
        self.miscviewAction.setChecked(True)
        self.view_changed()

        show_lines = QtWidgets.QMenu("show N lines", self)
        show_lines.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        ag = QActionGroup(show_lines)
        ag.setExclusive(True)
        show_lines_options = self.num_lines//5
        for i in range(1,show_lines_options+1):
            #dynamically create instance variable N_line_N and set it to an action
            setattr(self, "N_line_{}".format(str(i*5)), ag.addAction(QAction(str(i*5), show_lines, checkable=True)))
            show_lines.addAction(self.__dict__["N_line_{}".format(i*5)])
            self.__dict__["N_line_{}".format(i*5)].triggered.connect(self.num_lines_changed)
        self.num_lines_changed()

        update_interval = QtWidgets.QMenu("update interval (s)", self)
        update_interval.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        ag2 = QActionGroup(update_interval)
        ag2.setExclusive(True)

        for i in range(3):
            #dynamically create instance variable interval_S and connect it to action
            setattr(self, "interval_{}".format(str(i)), ag2.addAction(QAction(str(list([10,30,60])[i]), update_interval, checkable=True)))
            update_interval.addAction(self.__dict__["interval_{}".format(i)])
            self.__dict__["interval_{}".format(i)].triggered.connect(self.update_interval_changed)
        self.update_interval_changed()

        for i in range(self.num_lines):
            self.__dict__["line_{}".format(i)].current_line.clicked.connect(self.line_changed)
            self.__dict__["line_{}".format(i)].line_action.currentIndexChanged.connect(self.action_changed)
            # self.__dict__["line_{}".format(i)].line_action.connect(self.line_changed)
            # line.setStyleSheet("background: yellow")

        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        menubar.setNativeMenuBar(False)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.closeAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.exportScanParamsAction)
        fileMenu.addAction(self.importScanParamsAction)

        settingsMenu = menubar.addMenu(' &Settings')
        settingsMenu.addAction(self.initPVsAction)
        settingsMenu.addAction(self.initRecordAction)
        settingsMenu.addMenu(show_lines)
        settingsMenu.addMenu(update_interval)

        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(self.tomoAction)
        viewMenu.addAction(self.miscviewAction)

    def view_changed(self):
        self.header.start_time.setVisible(False)
        self.header.finish_time.setVisible(False)
        self.header.save_message.setVisible(False)
        self.header.r_center.setVisible(False)
        self.header.r_points.setVisible(False)
        self.header.r_width.setVisible(False)
        for line in range(self.num_lines):
            self.__dict__[self.line_names[line]].save_message.setVisible(False)
            self.__dict__[self.line_names[line]].start_time.setVisible(False)
            self.__dict__[self.line_names[line]].finish_time.setVisible(False)
            self.__dict__[self.line_names[line]].r_center.setVisible(False)
            self.__dict__[self.line_names[line]].r_points.setVisible(False)
            self.__dict__[self.line_names[line]].r_width.setVisible(False)

        if self.tomoAction.isChecked():
            self.header.r_center.setVisible(True)
            self.header.r_points.setVisible(True)
            self.header.r_width.setVisible(True)
            for line in range(self.show_lines):
                self.__dict__[self.line_names[line]].r_center.setVisible(True)
                self.__dict__[self.line_names[line]].r_points.setVisible(True)
                self.__dict__[self.line_names[line]].r_width.setVisible(True)

        if self.miscviewAction.isChecked():
            self.header.start_time.setVisible(True)
            self.header.finish_time.setVisible(True)
            self.header.save_message.setVisible(True)
            for line in range(self.show_lines):
                self.__dict__[self.line_names[line]].save_message.setVisible(True)
                self.__dict__[self.line_names[line]].start_time.setVisible(True)
                self.__dict__[self.line_names[line]].finish_time.setVisible(True)

        if not self.tomoAction.isChecked() and not self.miscviewAction.isChecked():
            self.setFixedWidth(self.view1)
        elif not self.tomoAction.isChecked() and self.miscviewAction.isChecked():
            self.setFixedWidth(self.view2)
        elif self.tomoAction.isChecked() and not self.miscviewAction.isChecked():
            self.setFixedWidth(self.view3)
        else:
            self.setFixedWidth(self.view4)

    def line_changed(self):
        checked_lines = []
        for line in range(self.show_lines):
            checked_lines.append(self.__dict__[self.line_names[line]].current_line.isChecked())
        last_clicked = self.sender()

        for line in range(self.show_lines):
            self.__dict__[self.line_names[line]].current_line.setChecked(False)
        last_clicked.setChecked(True)

    def action_changed(self):
        # TODO: change red scan trajectory un-scanned points to light gray

        row = self.sender()
        if row.currentIndex() == 1:
            row.parent().setStyleSheet("background: lavender")
        return
    def update_npts(self, line_number):
        x_step = eval(self.controls.x_step.text())
        y_step = eval(self.controls.y_step.text())
        x_npts = "-1"
        y_npts = "-1"
        # TODO: npts = round_to_whole number(width/step_size), npts*step_size = new_width

        current_line = self.__dict__[self.line_names[line_number]]
        x_width = np.abs(eval(current_line.x_width.text()))
        y_width = np.abs(eval(current_line.y_width.text()))
        if x_step < x_width:
            x_npts = np.ceil(x_width/x_step)
            x_width = x_npts*x_step
            current_line.x_points.setText(str(x_npts))
        elif x_step == x_width:
            x_npts = 2
            print("x_step same as width")
        else:
            x_npts = 1
            print("x_step larger than width")

        if y_step < y_width:
            y_npts = np.ceil(y_width/y_step)
            y_width = y_npts*y_step
        elif y_step == y_width:
            y_npts = 2
            print("y_step same as width")
        else:
            y_npts = 1
            print("y_step larger than width")

        if x_npts<=0 or y_npts<= 0:
            print("erorr setting npts from step size")
            return
        else:
            current_line.x_points.setText(str(x_npts))
            current_line.y_points.setText(str(y_npts))
            current_line.x_width.setText(str(x_width))
            current_line.y_width.setText(str(y_width))

    def points_clicked(self):
        if self.controls.x_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        if self.controls.y_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        else:
            for i in range(self.num_lines):
                if self.__dict__[self.line_names[i]].current_line.isChecked():
                    current_line = i
                    self.update_npts(current_line)

    def all_clicked(self):
        if self.controls.x_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        if self.controls.y_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        else:
            for i in range(self.show_lines):
                self.update_npts(i)

    def num_lines_changed(self):
        show_lines_options = self.num_lines//5
        for i in range(1, show_lines_options+1):
            if self.__dict__["N_line_{}".format(i*5)].isChecked():
                self.show_lines = i*5
                break
        for i in range(self.num_lines):
            if self.__dict__[self.line_names[i]].current_line.isChecked():
                last_checked = i
            self.__dict__[self.line_names[i]].setVisible(False)
        for i in range(self.show_lines):
            self.__dict__[self.line_names[i]].setVisible(True)

        if last_checked > self.show_lines:
            self.__dict__[self.line_names[last_checked]].current_line.setChecked(False)
            self.__dict__[self.line_names[self.show_lines-1]].current_line.setChecked(True)
        self.view_changed()
        return

    def update_interval_changed(self):
        intervals = [10,30,60]
        for i in range(3):
            if self.__dict__["interval_{}".format(i)].isChecked():
                self.update_interval = intervals[i]
                self.parent.thread2.timer = intervals[i]
                break
        return

    def closeEvent(self,event):
        #do other stuff if necessary, perhaps signal to batch_launcher to gracefully disconnect from PVS or something.
        #signal.emit("closing")
        self.save_session()

    def save_session(self):
        try:
            # print("autosaving session")
            cwd = os.path.dirname(os.path.abspath(__file__))+"/"
            file = self.session_file
            settings = {}
            save_list = []
            for i in range(self.num_lines):
                settings["line_{}".format(i)] = []

            for key in vars(self):
                if isinstance(vars(self)[key], Line):
                    line_object = vars(vars(self)[key])
                    for widget in line_object:
                        if isinstance(line_object[widget], QtWidgets.QRadioButton):
                            settings[key].append([widget, line_object[widget].isChecked()])
                        if isinstance(line_object[widget], QtWidgets.QPushButton):
                            if line_object[widget].isCheckable():
                                settings[key].append([widget, line_object[widget].isChecked()])
                        if isinstance(line_object[widget], QtWidgets.QComboBox):
                            settings[key].append([widget, line_object[widget].currentIndex()])
                        if isinstance(line_object[widget], QtWidgets.QLineEdit):
                            settings[key].append([widget, line_object[widget].text()])
                        if isinstance(line_object[widget], QtWidgets.QLabel):
                            settings[key].append([widget, line_object[widget].text()])

            with open(cwd+file, 'wb') as f:
                pickle.dump(["session",datetime.now(),settings], f)
                f.close()

        except IOError as e:
            print(e)
            print("cannot autosave upon close")

    def import_scan_params(self):
        try:
            fileName = QFileDialog.getOpenFileName(self, "Open File", QtCore.QDir.currentPath(), "All File (*);;CSV (*.csv *.CSV)")
            if fileName == "":
                raise IOError
            # field names
            fields = ['line number', ' scan type', 'trajectory', 'action', 'dwell time', 'x center', 'x points', 'x width',
                      'y center', 'y points', 'y width', 'comments', 'save message', 'start time', 'end time', 'r center', 'r points',
                      'r width', 'eta']

            rows = []
            with open(fileName[0], 'r') as f:
                reader_obj = csv.reader(f)
                for row in reader_obj:
                    rows.append(row)
                rows.pop(0)

            lines = [vars(self)[i] for i in self.line_names]
            scan_type = ["step", "fly"]
            trajectory = ["raster", "snake", "spiral", "lissajous", "custom"]
            action = ["skip", "normal", "pause", "done"]
            for idx, line in enumerate(lines):
                line.current_line.setText(rows[idx][0])
                line.scan_type.setChecked(scan_type.index(rows[idx][1]))
                line.scan_type.setText(rows[idx][1])
                line.trajectory.setCurrentIndex(trajectory.index(rows[idx][2]))
                line.line_action.setCurrentIndex(action.index(rows[idx][3]))
                line.dwell_time.setText(rows[idx][4])
                line.x_center.setText(rows[idx][5])
                line.x_points.setText(rows[idx][6])
                line.x_width.setText(rows[idx][7])
                line.y_center.setText(rows[idx][8])
                line.y_points.setText(rows[idx][9])
                line.y_width.setText(rows[idx][10])
                line.comments.setText(rows[idx][11])
                line.save_message.setText(rows[idx][12])
                line.start_time.setText(rows[idx][13])
                line.finish_time.setText(rows[idx][14])
                line.r_center.setText(rows[idx][15])
                line.r_points.setText(rows[idx][16])
                line.r_width.setText(rows[idx][17])
                line.line_eta.setText(rows[idx][18])
        except:
            return

    def export_scan_params(self):
        try:
            savedir = QFileDialog.getSaveFileName()[0]
            if len(savedir.split(".")) == 2:
                savedir = savedir.split(".")[0]
            else:
                pass

            if savedir == "":
                raise IOError

            # field names
            fields = ['line number', ' scan type', 'trajectory', 'action', 'dwell time', 'x center', 'x points', 'x width',
                      'y center', 'y points', 'y width', 'comments', 'save message', 'start time', 'end time', 'r center', 'r points',
                      'r width', 'eta']
            lines = []
            for key in vars(self):
                if isinstance(vars(self)[key], Line):
                    line_object = vars(vars(self)[key])
                    line_number = line_object["current_line"].text()
                    scan_type = line_object["scan_type"].text()
                    trajectory = line_object["trajectory"].currentText()
                    action = line_object["line_action"].currentText()
                    dwell_time = line_object["dwell_time"].text()
                    x_center = line_object["x_center"].text()
                    x_points = line_object["x_points"].text()
                    x_width = line_object["x_width"].text()
                    y_center = line_object["y_center"].text()
                    y_points = line_object["y_points"].text()
                    y_width = line_object["y_width"].text()
                    comments = line_object["comments"].text()
                    save_message = line_object["save_message"].text()
                    start_time = line_object["start_time"].text()
                    finish_time = line_object["finish_time"].text()
                    r_center = line_object["r_center"].text()
                    r_points = line_object["r_points"].text()
                    r_width = line_object["r_width"].text()
                    line_eta = line_object["line_eta"].text()
                    line_list = [line_number, scan_type, trajectory, action, dwell_time, x_center, x_points, x_width,
                                 y_center, y_points, y_width, comments, save_message, start_time, finish_time, r_center,
                                 r_points, r_width, line_eta]
                    lines.append(line_list)


            with open(savedir+".csv", 'w') as f:
                write = csv.writer(f)
                write.writerow(fields)
                write.writerows(lines)

        except IOError as e:
            print(e)
            print("cannot autosave upon close")
        return

    def restore_session(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        try:
            with open(current_dir+self.session_file,'rb') as f:
                contents = pickle.load(f)
                settings = contents[2]
                for line in settings:
                    for item in settings[line]:
                        widget = item[0]
                        value = item[1]
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QRadioButton):
                            vars(vars(self)[line])[widget].setChecked(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QPushButton):
                            vars(vars(self)[line])[widget].setChecked(value)
                            text = "fly" if value else "step"
                            vars(vars(self)[line])[widget].setText(text)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QComboBox):
                            vars(vars(self)[line])[widget].setCurrentIndex(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QLineEdit):
                            vars(vars(self)[line])[widget].setText(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QLabel):
                            vars(vars(self)[line])[widget].setText(value)
                            if widget == "line_eta":
                                hrs = int(value.split(":")[0])*60*60
                                min = int(value.split(":")[1])*60
                                sec = int(value.split(":")[2])
                                total_s = sec + min + hrs
                                vars(vars(self)[line])["eta"] = timedelta(seconds = total_s)
            f.close()
            return
        except:
            print("cannot autoload session, or file not found")
        return

    def open_session(self):
        #open all pkl files in cwd, set "last opened" status to 0 for all except current file.
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open .pkl", current_dir, "*.pkl")
        if file[0] == '':
            return
        try:
            with open(current_dir+self.session_file,'rb') as f:
                contents = pickle.load(f)
                settings = contents[2]
                for line in settings:
                    for item in settings[line]:
                        widget = item[0]
                        value = item[1]
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QRadioButton):
                            vars(vars(self)[line])[widget].setChecked(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QPushButton):
                            vars(vars(self)[line])[widget].setChecked(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QComboBox):
                            vars(vars(self)[line])[widget].setCurrentIndex(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QLineEdit):
                            vars(vars(self)[line])[widget].setText(value)
                        if isinstance(vars(vars(self)[line])[widget], QtWidgets.QLabel):
                            vars(vars(self)[line])[widget].setText(value)
            f.close()
            return
        except:
            print("cannot autoload session, or file not found")
        return
class Controls(QtWidgets.QWidget):
    def __init__(self):
        super(Controls, self).__init__()
        self.setupUi()

    def setupUi(self):
        size1 = 30
        size2 = 60
        size3 = 110
        size4 = 200
        size5 = 500

        exclude = set(locals())
        eta_lbl = QtWidgets.QLabel("ETA")
        eta_lbl.setFixedWidth(size1)
        self.eta = QtWidgets.QLabel("0")
        self.eta.setFixedWidth(size4)
        self.points = QtWidgets.QPushButton("pts")
        self.points.setFixedWidth(size1)
        self.points_all = QtWidgets.QPushButton("all")
        self.points_all.setFixedWidth(size1)
        self.x_step = QtWidgets.QLineEdit("0.002")
        self.x_step.setFixedWidth(size2)
        self.y_step = QtWidgets.QLineEdit("0.002")
        self.y_step.setFixedWidth(size2)
        points_lbl = QtWidgets.QLabel("calculate points for selected scan line")
        points_lbl.setFixedWidth(size4)
        points_all_lbl = QtWidgets.QLabel("calculate points for all scan lines")
        points_all_lbl.setFixedWidth(size4)
        x_step_lbl = QtWidgets.QLabel("X step")
        x_step_lbl.setFixedWidth(size2)
        y_step_lbl = QtWidgets.QLabel("Y step")
        y_step_lbl.setFixedWidth(size2)
        a1 = QtWidgets.QHBoxLayout()
        a1.addWidget(eta_lbl)
        a1.addWidget(self.eta)
        a2 = QtWidgets.QHBoxLayout()
        a2.addWidget(self.points)
        a2.addWidget(points_lbl)
        a3 = QtWidgets.QHBoxLayout()
        a3.addWidget(self.points_all)
        a3.addWidget(points_all_lbl)
        a4 = QtWidgets.QHBoxLayout()
        a4.addWidget(x_step_lbl)
        a4.addWidget(self.x_step)
        a4.addWidget(y_step_lbl)
        a4.addWidget(self.y_step)
        col1= QtWidgets.QVBoxLayout()
        col1.addLayout(a1)
        col1.addLayout(a2)
        col1.addLayout(a3)
        col1.addLayout(a4)
        col1.setContentsMargins(0,10,0,0)

        self.setup_btn = QtWidgets.QPushButton("setup")
        self.setup_btn.setFixedWidth(size2)
        self.import_btn = QtWidgets.QPushButton("Import")
        self.import_btn.setFixedWidth(size2)
        self.export_btn = QtWidgets.QPushButton("Export")
        self.export_btn.setFixedWidth(size2)
        self.zero_btn = QtWidgets.QPushButton("Zero")
        self.zero_btn.setFixedWidth(size2)
        self.zero_all_btn = QtWidgets.QPushButton("Zero all")
        self.zero_all_btn.setFixedWidth(size2)
        setup_lbl = QtWidgets.QLabel("PV setup window")
        setup_lbl.setFixedWidth(size3)
        import_lbl = QtWidgets.QLabel("from scan record")
        import_lbl.setFixedWidth(size3)
        export_lbl = QtWidgets.QLabel("to scan record")
        export_lbl.setFixedWidth(size3)
        zero_lbl = QtWidgets.QLabel("zero scan line")
        zero_lbl.setFixedWidth(size3)
        zero_all_lbl = QtWidgets.QLabel("zero all scans")
        zero_all_lbl.setFixedWidth(size3)
        b1 = QtWidgets.QVBoxLayout()
        b1.addWidget(self.setup_btn)
        b1.addWidget(self.import_btn)
        b1.addWidget(self.export_btn)
        b1.addWidget(self.zero_btn)
        b1.addWidget(self.zero_all_btn)
        b2 = QtWidgets.QVBoxLayout()
        b2.addWidget(setup_lbl)
        b2.addWidget(import_lbl)
        b2.addWidget(export_lbl)
        b2.addWidget(zero_lbl)
        b2.addWidget(zero_all_lbl)
        col2 = QtWidgets.QHBoxLayout()
        col2.addLayout(b1)
        col2.addLayout(b2)

        self.begin_btn = QtWidgets.QPushButton("Begin")
        self.begin_btn.setFixedWidth(size2)
        self.pause_btn = QtWidgets.QPushButton("Pause")
        self.pause_btn.setFixedWidth(size2)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setFixedWidth(size2)
        self.abort_btn = QtWidgets.QPushButton("Abort")
        self.abort_btn.setFixedWidth(size2)
        self.abort_all_btn = QtWidgets.QPushButton("Abort")
        self.abort_all_btn.setFixedWidth(size2)
        begin_lbl = QtWidgets.QLabel("begin batch scan")
        begin_lbl.setFixedWidth(size3)
        pause_lbl = QtWidgets.QLabel("pause batch scan")
        pause_lbl.setFixedWidth(size3)
        continue_lbl = QtWidgets.QLabel("resume from pause")
        continue_lbl.setFixedWidth(size3)
        abort_lbl = QtWidgets.QLabel("abort line")
        abort_lbl.setFixedWidth(size3)
        abort_all_lbl = QtWidgets.QLabel("abort all")
        abort_all_lbl.setFixedWidth(size3)

        c1 = QtWidgets.QVBoxLayout()
        c1.addWidget(self.begin_btn)
        c1.addWidget(self.pause_btn)
        c1.addWidget(self.continue_btn)
        c1.addWidget(self.abort_btn)
        c1.addWidget(self.abort_all_btn)
        c2 = QtWidgets.QVBoxLayout()
        c2.addWidget(begin_lbl)
        c2.addWidget(pause_lbl)
        c2.addWidget(continue_lbl)
        c2.addWidget(abort_lbl)
        c2.addWidget(abort_all_lbl)
        col3 = QtWidgets.QHBoxLayout()
        col3.addLayout(c1)
        col3.addLayout(c2)

        self.message_window = QtWidgets.QTextEdit("")
        self.message_window.setFixedWidth(700)
        self.message_window.setStyleSheet("background: beige; color: black")
        self.message_window.setReadOnly(True)

        self.status_bar = QtWidgets.QLabel("status bar")
        self.status_bar.setFixedWidth(700)
        self.status_bar.setStyleSheet("background: lightgray; color: black")

        control_layout = QtWidgets.QHBoxLayout()
        control_layout.addLayout(col1)
        control_layout.addLayout(col2)
        control_layout.addLayout(col3)
        control_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        controlframe = QtWidgets.QFrame()
        controlframe.setLayout(control_layout)
        controlframe.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);"
                                   "border-width: 1;"
                                   "border-radius: 3;"
                                   "border-style: solid;"
                                   "border-color: rgb(10, 10, 10)}")
        controlframe.setContentsMargins(0,0,0,0) #left, top,right, bottom
        controlframe.setFixedWidth(700)

        combined = QtWidgets.QVBoxLayout()
        combined.addWidget(controlframe)
        combined.addWidget(self.status_bar)
        combined.addWidget(self.message_window)

        combined2 = QtWidgets.QHBoxLayout()
        combined2.addLayout(combined)

        self.view_box = ImageView()
        combined2.addWidget(self.view_box)

        include = list(set(locals())-exclude)
        for key in include:
            item = locals()[key]
            if isinstance(item,QtWidgets.QLabel):
                item.setStyleSheet("color: black; border-color: white")

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QLineEdit):
                item.textChanged.connect(self.validate_params)
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QtWidgets.QLabel):
                item.setStyleSheet("QLabel {background-color: lightgray;" 
                                           "color: black;"
                                           "border-width: 0;"
                                           "border-radius: 3;"
                                           "border-style: solid;"
                                           "border-color: white}")
                # item.setStyleSheet("background: lightgray;color: black; border-radius: 4;")
            elif isinstance(item,QtWidgets.QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QtWidgets.QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            elif isinstance(item,QtWidgets.QRadioButton):
                item.setStyleSheet("background: white;color: black; border-radius: 4")
            else:
                pass

        self.setStyleSheet("background: white")
        self.setLayout(combined2)

    def validate_params(self):
        for key in self.__dict__:
            item = getattr(self, key)
            if isinstance(item, QtWidgets.QLineEdit):
                try:
                    value = eval(item.text())
                    if value<=0:
                        if item.isEnabled():
                            item.setStyleSheet("background: lightcoral; color: black; border-radius: 4")
                        else:
                            item.setStyleSheet("background: lightblue; color: lightblue; border-radius: 4")
                    else:
                        if item.isEnabled():
                            item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
                        else:
                            item.setStyleSheet("background: lightblue; color: lightblue; border-radius: 4")

                except:
                    item.setStyleSheet("background: lightcoral; color: black; border-radius: 4")
            else:
                pass


class Header(QtWidgets.QWidget):
    def __init__(self):
        super(Header, self).__init__()
        self.setupUi()

    def setupUi(self):
        size1 = 30
        size2 = 60
        size3 = 220
        size4 = 120
        size5 = 75
        line = QtWidgets.QHBoxLayout()
        self.line = QtWidgets.QLabel("line")
        self.line.setFixedWidth(size1)
        self.scan_type = QtWidgets.QLabel("scan \ntype")
        self.scan_type.setFixedWidth(size1)
        self.trajectory = QtWidgets.QLabel("trajectory")
        self.trajectory.setFixedWidth(size5)
        self.line_action = QtWidgets.QLabel("action")
        self.line_action.setFixedWidth(size5)
        self.dwell_time = QtWidgets.QLabel("dwell \n(ms)")
        self.dwell_time.setFixedWidth(size1)
        self.x_center = QtWidgets.QLabel("x center")
        self.x_center.setFixedWidth(size2)
        self.x_points = QtWidgets.QLabel("x points")
        self.x_points.setFixedWidth(size2)
        self.x_width = QtWidgets.QLabel("x width")
        self.x_width.setFixedWidth(size2)
        self.y_center = QtWidgets.QLabel("y center")
        self.y_center.setFixedWidth(size2)
        self.y_points = QtWidgets.QLabel("y points")
        self.y_points.setFixedWidth(size2)
        self.y_width = QtWidgets.QLabel("y width")
        self.y_width.setFixedWidth(size2)
        self.comments = QtWidgets.QLabel("comments")
        self.comments.setFixedWidth(size3)
        self.save_message = QtWidgets.QLabel("save message")
        self.save_message.setFixedWidth(size3)
        self.save_message.setVisible(False)
        self.start_time = QtWidgets.QLabel("start time")
        self.start_time.setFixedWidth(size4)
        self.start_time.setVisible(False)
        self.finish_time = QtWidgets.QLabel("finish time")
        self.finish_time.setFixedWidth(size4)
        self.finish_time.setVisible(False)
        self.r_center = QtWidgets.QLabel("r center")
        self.r_center.setFixedWidth(size2)
        self.r_center.setVisible(False)
        self.r_points = QtWidgets.QLabel("r points")
        self.r_points.setFixedWidth(size2)
        self.r_points.setVisible(False)
        self.r_width = QtWidgets.QLabel("r width")
        self.r_width.setFixedWidth(size2)
        self.r_width.setVisible(False)
        self.global_eta = QtWidgets.QLabel("eta H:M:S")
        self.global_eta.setFixedWidth(size2)

        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(12)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item,QtWidgets.QLabel):
                item.setStyleSheet("background: white;color: black; border-color: white")
                item.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                item.setFont(myFont)
            else:
                pass

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QLabel):
                line.addWidget(item)
            else:
                pass
        line.setContentsMargins(0,10,0,0)
        self.setLayout(line)

class Line(QtWidgets.QWidget):
    paramsChangedSig = QtCore.pyqtSignal(int)
    def __init__(self):
        super(Line, self).__init__()
        self.setupUi()
        self.make_pretty()
        self.trajectory_arr = []
        self.eta = timedelta(seconds=int(0))
        self.valid = True
        self.x_hlm = 100
        self.x_llm = -100
        self.x_vmax = 5
        self.x_vmin = 0.4
        self.y_hlm = 1000
        self.y_llm = -1000
        self.r_hlm = 1000
        self.r_llm = -1000
        self.x_res = 0.01
        self.y_res = 0.01
    def setupUi(self):
        size1 = 30
        size2 = 60
        size3 = 220
        size4 = 120
        size5 = 75
        line = QtWidgets.QHBoxLayout()
        self.setStyleSheet("background: white")
        self.current_line = QtWidgets.QRadioButton()
        self.current_line.setFixedWidth(size1)
        self.scan_type = QtWidgets.QPushButton("step", checkable = True)
        self.scan_type.setFixedWidth(size1)
        self.trajectory = QtWidgets.QComboBox()
        trajectories = ["raster","snake","spiral","lissajous","custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedWidth(size5)
        self.line_action = QtWidgets.QComboBox()
        actions = ["skip","normal", "pause", "done"]
        self.line_action.addItems(actions)
        self.line_action.setFixedWidth(size5)
        self.dwell_time = QtWidgets.QLineEdit("0")
        self.dwell_time.setFixedWidth(size1)
        self.x_center = QtWidgets.QLineEdit("0")
        self.x_center.setFixedWidth(size2)
        self.x_points = QtWidgets.QLineEdit("0")
        self.x_points.setFixedWidth(size2)
        self.x_width = QtWidgets.QLineEdit("0")
        self.x_width.setFixedWidth(size2)
        self.y_center = QtWidgets.QLineEdit("0")
        self.y_center.setFixedWidth(size2)
        self.y_points = QtWidgets.QLineEdit("0")
        self.y_points.setFixedWidth(size2)
        self.y_width = QtWidgets.QLineEdit("0")
        self.y_width.setFixedWidth(size2)
        self.comments = QtWidgets.QLineEdit("")
        self.comments.setFixedWidth(size3)
        self.save_message = QtWidgets.QLabel("")
        self.save_message.setFixedWidth(size3)
        self.save_message.setVisible(False)
        self.start_time = QtWidgets.QLabel("")
        self.start_time.setFixedWidth(size4)
        self.start_time.setVisible(False)
        self.finish_time = QtWidgets.QLabel("")
        self.finish_time.setFixedWidth(size4)
        self.finish_time.setVisible(False)
        self.r_center = QtWidgets.QLineEdit("0")
        self.r_center.setFixedWidth(size2)
        self.r_center.setVisible(False)
        self.r_points = QtWidgets.QLineEdit("0")
        self.r_points.setFixedWidth(size2)
        self.r_points.setVisible(False)
        self.r_width = QtWidgets.QLineEdit("0")
        self.r_width.setFixedWidth(size2)
        self.r_width.setVisible(False)
        self.line_eta = QtWidgets.QLabel("00:00:00")
        self.line_eta.setFixedWidth(size2)


        for key in self.__dict__:
            item = getattr(self,key)
            if key == "trajectory":
                item.currentIndexChanged.connect(self.trajector_changed)
            if key == "line_action":
                item.currentIndexChanged.connect(self.line_valid)
            if isinstance(item, QtWidgets.QLineEdit):
                item.textChanged.connect(self.validate_params)
                item.textChanged.connect(self.calculate_line_eta)
                item.returnPressed.connect(self.calculate_line_eta)
                item.editingFinished.connect(self.params_changed)
            elif isinstance(item,QtWidgets.QPushButton):
                item.clicked.connect(self.scan_type_clicked)
                item.clicked.connect(self.calculate_line_eta)
            if isinstance(item, QtWidgets.QHBoxLayout):
                pass
            if isinstance(item, QtCore.pyqtSignal):
                pass
            else:
                line.addWidget(item)
        line.setContentsMargins(0,0,0,0)

        self.setLayout(line)
    def trajector_changed(self):
        trajectory = self.sender()
        if trajectory.currentText() == "raster" or trajectory.currentText() == "snake" :
            self.x_center.setEnabled(True)
            self.x_points.setEnabled(True)
            self.x_width.setEnabled(True)
            self.y_center.setEnabled(True)
            self.y_points.setEnabled(True)
            self.y_width.setEnabled(True)
        elif self.trajectory.currentText() == "spiral":
            self.x_center.setEnabled(True)
            self.x_points.setEnabled(True)
            self.x_width.setEnabled(True)
            self.y_center.setEnabled(False)
            self.y_points.setEnabled(False)
            self.y_width.setEnabled(False)
        elif self.trajectory.currentText() == "lissajous":
            self.x_center.setEnabled(True)
            self.x_points.setEnabled(True)
            self.x_width.setEnabled(True)
            self.y_center.setEnabled(False)
            self.y_points.setEnabled(False)
            self.y_width.setEnabled(False)
        elif self.trajectory.currentText() == "custom":
            self.x_center.setEnabled(False)
            self.x_points.setEnabled(False)
            self.x_width.setEnabled(False)
            self.y_center.setEnabled(False)
            self.y_points.setEnabled(False)
            self.y_width.setEnabled(False)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QLineEdit):
                if item.isEnabled():
                    item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
                else:
                    item.setStyleSheet("background: lightblue; color: lightblue; border-radius: 4")
        self.validate_params()

    def scan_type_clicked(self):
        button = self.sender()
        if button.isChecked():
            button.setText("fly")
            self.trajectory.clear()
            trajectories = ["raster", "snake"]
            self.trajectory.addItems(trajectories)
        else:
            button.setText("step")
            self.trajectory.clear()
            trajectories = ["raster", "snake", "spiral", "lissajous", "custom"]
            self.trajectory.addItems(trajectories)

    def params_changed(self):
        self.paramsChangedSig.emit(eval(self.objectName))

    def validate_params(self):
        for key in self.__dict__:
            item = getattr(self, key)
            if isinstance(item, QtWidgets.QLineEdit):
                try:
                    if key == "comments":
                        pass
                    elif not item.isEnabled():
                        item.setStyleSheet("background: lightblue; color: lightblue; border-radius: 4")

                    elif eval(item.text())%1>=0 and (key == "r_center" or key == "x_center" or key == "y_center" or key == "x_width" or key == "y_width" or key == "r_width"):
                        item.setStyleSheet("background: lightblue; color: black; border-radius: 4")

                    elif (eval(item.text())>=0 and int(item.text())%1==0) and (key == "x_points" or key == "y_points" or key == "r_points"):
                        item.setStyleSheet("background: lightblue; color: black; border-radius: 4")

                    elif eval(item.text()) > 0 and key == "dwell_time":
                        item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
                    else:
                        item.setStyleSheet("background: lightcoral; color: black; border-radius: 4")
                except:
                    item.setStyleSheet("background: lightcoral; color: black; border-radius: 4")

        self.line_valid()

    def line_valid(self):
        self.valid = True
        self.setStyleSheet("background: white")
        self.setAutoFillBackground(True)

        if self.line_action.currentText() == "normal" or self.line_action.currentText() == "pause":
            for key in self.__dict__:
                item = getattr(self, key)
                if isinstance(item, QtWidgets.QLineEdit) and key != "comments" and item.isEnabled() and item.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
                    self.valid = False
                    self.setStyleSheet("background: lightsalmon")
                    self.setAutoFillBackground(True)
                    return

                if isinstance(item, QtWidgets.QLineEdit) and (key == "dwell_time" or key == "x_width" or key == "y_width" or key == "x_points" or key == "y_points") and item.isEnabled():
                    if eval(item.text()) == 0:
                        self.valid = False
                        self.setStyleSheet("background: lightsalmon")
                        self.setAutoFillBackground(True)
                        return

            if not self.motor_limits_valid():
                self.valid = False
                self.setStyleSheet("background: lightsalmon")
                self.setAutoFillBackground(True)
                return

    def motor_limits_valid(self):
        x_hlm = self.x_hlm
        x_llm = self.x_llm
        x_vmax = self.x_vmax
        x_vmin = self.x_vmin
        x_res = self.x_res
        y_hlm = self.y_hlm
        y_llm = self.y_llm
        y_res = self.y_res
        r_hlm = self.r_hlm
        r_llm = self.r_llm
        x_center = eval(self.x_center.text())
        y_center = eval(self.y_center.text())
        r_center = eval(self.r_center.text())
        x_width = eval(self.x_width.text())
        y_width = eval(self.y_width.text())
        r_width = eval(self.r_width.text())
        x_points = eval(self.x_points.text())
        y_points = eval(self.y_points.text())
        r_points = eval(self.r_points.text())
        dwell_time = eval(self.dwell_time.text())

        velocity_violation = False
        scan = [self.x_center, self.y_center, self.x_width, self.y_width, self.x_points, self.y_points, self.dwell_time]

        try:
            x_step = abs(x_width/x_points)
            y_step = abs(y_width/y_points)
            if x_vmax == 0:
                velocity_violation = False
            elif x_step/(dwell_time/1000) > x_vmax:
                velocity_violation = True

            if x_step < x_res:
                print("step size smaller than x_motor resolution, cannot run scan. ")
                return False

            if y_step < y_res:
                print("step size smaller than y_motor resolution, cannot run scan. ")
                return False
        except ZeroDivisionError:
            velocity_violation = True
            pass



        if (x_center - abs(x_width)/2) <= x_llm or (x_center + abs(x_width)/2) >= x_hlm or (y_center - abs(y_width)/2) <= y_llm or (y_center + abs(y_width)/2) >= y_hlm:
            print((x_center - abs(x_width)/2), x_llm, (x_center + abs(x_width)/2), x_hlm, (y_center - abs(y_width)/2), y_llm, (y_center + abs(y_width)/2), y_hlm)
            print("scan outside motor limits")
            #TODO: Figure out how to add r_motor logic.
            #(r_center - r_width / 2) <= r_llm or (r_center + r_width / 2) >= r_hlm:
            return False

        if velocity_violation:
            print("step size / dwell time exceeds positioner velocity")
            return False
        else:
            return True

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
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::checked {background-color: orchid;}")
                # item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            elif isinstance(item,QtWidgets.QRadioButton):
                item.setStyleSheet("background: white;color: black; border-radius: 4")
            else:
                pass
        return
    def calculate_line_eta(self):
        hms = str(timedelta(seconds=int(0)))
        #if any textedit in line is invalid (lihtcoral), return eta of "invalid"
        invalid = 0
        if self.dwell_time.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.x_center.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.x_points.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.x_width.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.y_center.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.y_points.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.y_width.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.r_center.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.r_points.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if self.r_width.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1

        if invalid:
            self.line_eta.setText(hms)
            self.eta= timedelta(seconds=0)
            return
        dwell = float(self.dwell_time.text())/1000
        x_points = int(self.x_points.text())
        x_width = float(self.x_width.text())
        y_points = int(eval(self.y_points.text()))
        y_width = float(eval(self.y_width.text()))
        y_points = 0
        r_points = 0
        seconds_total = 0
        scan_type = self.scan_type.text()
        trajectory = self.trajectory.currentText()
        overhead = 1.18

        if self.r_center.isVisible():
            r_points = int(eval(self.r_points.text()))
            r_width = float(eval(self.r_width.text()))

        if trajectory == "raster" or trajectory == "snake":
            width_not_zero = (x_width*y_width>0)*1
            seconds_total = dwell*x_points*y_points*overhead*width_not_zero + (2*y_points)

        if trajectory == "spiral" or trajectory == "lissajous" or trajectory == "custom":
            seconds_total = dwell*x_points*overhead

        if self.r_center.isVisible() and r_points > 0:
            seconds_total = seconds_total*r_points

        hms = str(timedelta(seconds=int(seconds_total)))
        self.line_eta.setText(hms)
        try:
            hrs = int(hms.split(":")[0]) * 60 * 60
            min = int(hms.split(":")[1]) * 60
            sec = int(hms.split(":")[2])
            total_s = sec + min + hrs
        except:
            return
        self.eta = timedelta(seconds=total_s)
        return

class ImageView(pyqtgraph.GraphicsLayoutWidget):
    def __init__(self):
        super(ImageView, self).__init__()
        self.initUI()

    def initUI(self):
        self.p1 = self.addPlot(title="current scan")
        styles = {'color': 'r', 'font-size': '20px'}
        self.p1.setLabel('left', 'Y-pos', **styles)
        self.p1.setLabel('bottom', 'X-pos', **styles)
        self.p1.setTitle("scan trajectory", color="b", size="20pt")

        self.p1.x = [0,0,0,0]
        self.p1.y = [0,0,0,0]
        pen = pyqtgraph.mkPen(color="w")
        # self.p1.setXRange(0, 10, padding=0)
        # self.p1.setYRange(0,10, padding=0)
        self.data_trajectory = self.p1.plot([0,1,2,3],[0,0,0,0], pen=pen, symbol='o', symbolSize=5, symbolBrush="r")
        self.data_line = self.p1.plot([0,1,2,3],[0,1,2,3], pen=pen, symbol='o', symbolSize=5, symbolBrush="b")
        self.projView = pyqtgraph.ImageItem(axisOrder = "row-major")
        self.p1.setMouseEnabled(x=False, y=False)
        self.vb = self.p1.getViewBox()
        self.vb.setBackgroundColor((255,255,255))
        self.setBackground("w")

    def plott(self, x, y):
        self.data_line.setData(x, y)

    def wheelEvent(self, ev):
        #empty function, but leave it as it overrides some other unwanted functionality.
        pass