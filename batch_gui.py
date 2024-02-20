

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
import batch_settings
import sys
import psutil

#GUI structure:
#   Lines()
#   Controls()
#   ImageView()

#TODO: set the motor minimum velocity to 0.01 for longer dwell times.
#TODO: current scan line background (yellow) dissappears if any of the text fields are modified.
#TODO: FIX global ETA
#DONE: npts = round_to_whole number(width/step_size), npts*step_size = new_width
#DONE: zero dwell time turns red even if line is set to skip.
#DONE: save message gets written even if scan was skipped.
#TODO: set line background to light gray if line set to normal
#TODO: dynamically adjust font size to fit inside box

class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)
    def write(self, text):
        self.newText.emit(str(text))
class BatchScanGui(QtWidgets.QWidget):
    def __init__(self):
        super(QtWidgets.QWidget, self).__init__()
        sys.stdout = Stream(newText=self.onUpdateText)

        # self.app = app
        self.view1 = 900
        self.view2 = 1600
        self.view3 = 1330
        self.view4 = 1830
        self.active_line = -1
        self.session_file = "default_session.pkl"

        self.update_interval = 10
        self.scan_ids = []
        self.id_counter = 0
        self.initUI()
        self.show()

    def initUI(self):
        # self.header = Header()
        self.controls = Controls()
        self.batch_widget = self.make_batch_widget(5)
        self.settings = batch_settings.ScanSettings()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.batch_widget)
        layout.addWidget(self.controls)
        layout.setSpacing(0)

        self.setLayout(layout)
        self.setStyleSheet("background: white")
        self.line_1.current_line.setChecked(True)
        self.closeAction = QAction(' &close', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        # self.view_changed()

        self.closeAction.triggered.connect(sys.exit)
        self.settings.settings_closed_sig.connect(self.settings_changed)
        self.controls.connect_server_btn.clicked.connect(self.connect_server_clicked)
        self.controls.setup_btn.clicked.connect(self.settings.show)
        self.controls.setup_btn.clicked.connect(self.settings.openEvent)
        self.controls.points_all.clicked.connect(self.all_clicked)
        self.controls.points.clicked.connect(self.points_clicked)
        self.controls.abort_btn.clicked.connect(self.abort_clicked)
        self.controls.zero_all_btn.clicked.connect(self.zero_all_clicked)
        self.controls.zero_btn.clicked.connect(self.zero_clicked)
        self.controls.continue_btn.clicked.connect(self.continue_clicked)
        self.controls.pause_btn.clicked.connect(self.pause_clicked)


        # TODO: widget class does not have menu bar, add these as buttons or under settings.
        # fileMenu.addAction(self.exportScanParamsAction)
        # fileMenu.addAction(self.importScanParamsAction)

    def onUpdateText(self, text):
        cursor = self.controls.message_window.textCursor()
        cursor.insertText(text)
        self.controls.message_window.setTextCursor(cursor)
        self.controls.message_window.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__


    def add_line(self):
        self.id_counter = self.id_counter + 1
        self.scan_ids.append(self.id_counter)
        scan_id = self.scan_ids[-1]
        setattr(self, "line_{}".format(scan_id), Line(scan_id))
        line = self.__dict__["line_{}".format(scan_id)]
        line.current_line.clicked.connect(self.line_changed)
        line.current_line.setText(str(len(self.scan_ids)))
        line.setAutoFillBackground(True)
        line.addlinesig.connect(self.add_line)
        line.deletelinesig.connect(self.delete_line)
        line.duplicatelinesig.connect(self.duplicate_line)
        self.lines_layout.addWidget(line, alignment=QtCore.Qt.AlignLeft)
        # self.view_changed()
        pass

    def delete_line(self, scan_id):
        #TODO: find line by index, delete it somehow

        # self.lines_layout.itemAt(line_idx).setParent(None)
        # self.lines_layout.removeItem(self.lines_layout.itemAt(line_idx))
        line = self.__dict__["line_{}".format(scan_id)]
        current_line = int(line.current_line.text())
        line.deleteLater()
        self.lines_layout.removeWidget(line)
        delattr(self, "line_{}".format(scan_id))
        self.scan_ids.remove(scan_id)

        #TODO: update other line names
        ids = self.get_scan_ids()
        some_scan_ids = [i for i in ids if i > scan_id]
        for i in some_scan_ids:
          line = self.get_line(i)
          line["current_line"].setText(str(int(line["current_line"].text())-1))

        # self.view_changed()

    def duplicate_line(self, scan_id):
        self.add_line()
        params = self.get_scan(scan_id)
        self.update_scan_line(params,self.scan_ids[-1])
        # self.view_changed()
        pass
    def make_batch_widget(self, num_lines):
        batch_widget = QScrollArea()
        scroll_widget = QWidget()
        self.lines_layout = QtWidgets.QVBoxLayout()

        for i in range(num_lines):
            self.add_line()
        scroll_widget.setLayout(self.lines_layout)
        scroll_widget.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);border-width: 1;border-radius: 3;border-style: solid;border-color: rgb(10, 10, 10)}")
        scroll_widget.setMaximumWidth(1700)
        batch_widget.setWidget(scroll_widget)
        batch_widget.setWidgetResizable(True)

        return batch_widget
    def validate_line(self, line):
        #TODO: get scan params from line params = line.params
        # is_valid = self.client.validate_params(params)
        pass

    def get_line(self, scan_id):
        lines = self.get_lines()
        for row in lines:
            if row["id"] == scan_id:
                line = row
                return line
        return None

    def get_checked_line(self,):
        lines = self.get_lines()
        for row in lines:
            if row["current_line"].isChecked():
                line = row
                return line, line["id"]
        return None

    def get_scan_ids(self):
        lines = self.get_lines()
        scan_ids = []
        for line in lines:
            scan_ids.append(int(line["id"]))
        return scan_ids

    def get_scan(self, line_idx):
        line = self.get_line(line_idx)
        params = self.get_params()
        scan = {}
        for key in params:
            if key == "detectors":
                scan[key] = line["detectors"].checked_items()
            elif key == "trajectory":
                scan[key] = line["trajectory"].currentIndex()
            else:
                scan[key] = line[key].text()
        return scan

    def update_scan_line(self,scan,scan_id):
        line = self.get_line(scan_id)
        for key in scan.keys():
            if key == "current_line":
                pass
            elif key == "detectors":
                line[key].check_selected(scan[key])
            elif key == "trajectory":
                line[key].setCurrentIndex(scan[key])
            else:
                line[key].setText(scan[key])

    def update_plot(self):
        #TODO: get scanID
        #TOOO: get trajectory
        #TODO: get scan_progress
        #TODO: set_plot(trajectory[:scan_progress]
        # self.controls.view_box.plott(x_arr[:idx], y_arr[:idx])
        pass

    def get_scan_progress(self):
        #TODO: self.client.get_scan_progress(scan_id)
        pass
    def get_trajectory(self):
        #TODO: current_line = self.get_current_line()
        #TODO: xpts, ypts= self.client.get_trajectory(current_line.scan_id)
        pass

    def set_plot(self):
        try:
            x_arr, y_arr = self.get_trajectory()
            self.controls.view_box.data_trajectory.setData(x_arr, y_arr)
            self.controls.view_box.p1.setXRange(x_arr.min(),x_arr.max())
            self.controls.view_box.p1.setYRange(y_arr.min(),y_arr.max())
        except:
            return
    def settings_changed(self):
        scan_generator = self.settings.setup_window.scan_generator.text()
        pv_status = self.settings.pv_status

        self.xrf_connected = pv_status["xrf"][2]
        self.eiger_connected = pv_status["eiger"][2]
        self.struck_connected = pv_status["struck"][2]
        self.x_motor_connected = pv_status["x_motor"][2]
        self.y_motor_connected = pv_status["y_motor"][2]
        self.r_motor_connected = pv_status["r_motor"][2]

        if scan_generator == "profile move":
            # self.controls.import_btn.setVisible(False)
            # self.controls.export_btn.setVisible(False)
            # self.controls.import_lbl.setVisible(False)
            # self.controls.export_lbl.setVisible(False)
            self.controls.backup_scanrecord_btn.setVisible(False)
            self.controls.backup_scanrecord_lbl.setVisible(False)
            self.trajectory = self.settings.setup_window.trajectory_cbbx.currentText()
            self.profile_move_connected = pv_status["profile_move"][2]
            self.softgluezynq_connected = pv_status["softgluezynq"][2]
            if not self.profile_move_connected or not self.softgluezynq_connected or not self.x_motor_connected or not self.y_motor_connected:
                self.controls.begin_btn.setDisabled(True)
                self.controls.pause_btn.setDisabled(True)
                self.controls.continue_btn.setDisabled(True)
            else:
                self.controls.begin_btn.setDisabled(False)
                self.controls.pause_btn.setDisabled(False)
                self.controls.continue_btn.setDisabled(False)
            if not self.xrf_connected:
                # TODO: skip xspress3 setup in backend.
                pass
            if not self.eiger_connected:
                # TODO: skip eiger setup in backend.
                pass

        elif scan_generator == "ACS program buffer":
            pass
            # self.controls.import_btn.setVisible(False)
            # self.controls.export_btn.setVisible(False)
            # self.controls.import_lbl.setVisible(False)
            # self.controls.export_lbl.setVisible(False)
            # self.trajectory = self.settings.setup_window.trajectory_cbbx.currentText()
            # self.softgluezynq_connected = pv_status["softgluezynq"][2]
            # if not self.softgluezynq_connected or not self.x_motor_connected or not self.y_motor_connected:
            #     self.controls.begin_btn.setDisabled(True)
            #     self.controls.pause_btn.setDisabled(True)
            #     self.controls.continue_btn.setDisabled(True)
            # else:
            #     self.controls.begin_btn.setDisabled(False)
            #     self.controls.pause_btn.setDisabled(False)
            #     self.controls.continue_btn.setDisabled(False)
            # if not self.xrf_connected:
            #     # TODO: skip xspress3 setup in backend.
            #     pass
            # if not self.eiger_connected:
            #     # TODO: skip eiger setup in backend.
            #     pass

        elif scan_generator == "scan record":

            self.controls.backup_scanrecord_btn.setVisible(True)
            self.controls.backup_scanrecord_lbl.setVisible(True)
            self.trajectory = "raster"
            self.inner_before_wait_connected = pv_status["inner_before_wait"][2]
            self.inner_after_wait_connected = pv_status["inner_after_wait"][2]
            self.outer_before_wait_connected = pv_status["outer_before_wait"][2]
            self.outer_after_wait_connected = pv_status["outer_after_wait"][2]
            self.delay_calc_connected = pv_status["delay_calc"][2]
            self.save_data_connected = pv_status["save_data"][2]
            self.scan_inner_connected = pv_status["scan_inner"][2]
            self.scan_outer_connected = pv_status["scan_outer"][2]
            self.scan_inner_extra_connected = pv_status["scan_inner_extra"][2]
            self.scan_outer_extra_connected = pv_status["scan_outer_extra"][2]
            if not self.inner_before_wait_connected or not self.inner_after_wait_connected or not self.outer_before_wait_connected or not self.outer_after_wait_connected:
                #TODO: use different way of checking before and after scans.
                pass

            if not self.delay_calc_connected:
                #TODO: signal to backend to change positioner from delay_calc to regular positioner PV
                pass
            if not self.scan_inner_connected or not self.scan_outer_connected or not self.save_data_connected or not self.struck_connected or not self.x_motor_connected or not self.y_motor_connected:
                # self.controls.begin_btn.setDisabled(True)
                # self.controls.pause_btn.setDisabled(True)
                # self.controls.continue_btn.setDisabled(True)
                pass
            else:
                # self.controls.begin_btn.setDisabled(False)
                # self.controls.pause_btn.setDisabled(False)
                # self.controls.continue_btn.setDisabled(False)
                pass

    def connect_server_clicked(self):
        ##check if server already running with PID"
        # ps -ef | grep "python server.py"
        ##if server runing, attempt to connec to it"
        pid = self.command_response("ps -ef | grep \"python server.py\" ")

        PROCNAME = "server.py"

        pids = {}
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.name() == PROCNAME:
                pids[proc.name()] = proc.pid

        if len(pids) == 0:
            print("no server in pid list, starting new server instance")
        elif len(pids) == 1:
            print("server pid found, atempting to connect")
        else:
            print("more than one server pid found, consider terminating one.")
            print(pids)

        cwd = os.getcwd() + "/"
        python_path = self.command_response("where python")
        if python_path == "":
            python_path = self.command_response("which python")

        if python_path == "":
            print("could not connect to server")
            return

        command = "{}python", "{}server.py".format(python_path, cwd)
        self.command_detatch(command)

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

    def command_detatch(self, command):
        # subprocess.call("{}python", "{}server.py".format(python_path,cwd), shell=True)
        # TODO: check if this starts and detaches from main process.
        subprocess.Popen([command], shell=True)
        return

    def abort_clicked(self):

        #TODO:  get ongoing scan ID
        #TODO:  send abort request
        #TODO:  update save data message for line matching scanID with "aborted scan XXXX"
        #TODO:  aborting does not atuomatically continue other ququed scans, you have to press begin again.

        # scanID = self.backeg.get_scan_id()
        # self.backend.abort_scan()
        # savedata_message = self.backend.get_savedata_message()
        # self.lines[scanID].save_message.setText(savedata_message)
        pass

    def continue_clicked(self):
        #TODO:  if server connected, continue, else return and print("server not connected")
        #TODO:  get ongoing scan ID
        #TODO: sent coninue request
        #TODO: get scan status, update gui


        # scanID = self.backeg.get_scan_id()
        # self.backend.continue_scan()
        # self.lines[scanID].status.setText(savedata_message)
        pass

    def pause_clicked(self):
        #TODO: if server connected, pause, else return and print("server not connected")
        #TODO: get ongoing scan ID
        #TODO: sent pause request
        #TODO: get scan status
        #TODO: update gui
        pass

    def begin_clicked(self):

        # TODO: if server connected, pause, else return and print("server not connected")
        # TODO: get_scan_id
        # TODO: send begin_scan request
        # TODO: get scan status
        # TODO: update gui
        pass

    def zero_all_clicked(self):
        lines = self.get_lines()
        for line in lines:
            for widget in line.keys():
                if isinstance(line[widget], QtWidgets.QLabel) or isinstance(line[widget], QtWidgets.QLineEdit):
                    if widget == "line_action":
                        line[widget].setText("queue")
                    elif widget == "line_eta":
                        line[widget].setText("00:00:00")
                    else:
                        line[widget].setText("")

    def zero_clicked(self):
        line, scan_id = self.get_checked_line()
        for widget in line.keys():
            if isinstance(line[widget], QtWidgets.QLabel) or isinstance(line[widget], QtWidgets.QLineEdit):
                if widget == "line_action":
                    line[widget].setText("queue")
                elif widget == "line_eta":
                    line[widget].setText("00:00:00")
                else:
                    line[widget].setText("")

    def line_color(self, line_idx, color="white"):
        if color == "red" or color == "white":
            line = [vars(self)[i] for i in self.line_names][line_idx]
            line.setStyleSheet("background: {}".format(color))
            line.setAutoFillBackground(True)
        else:
            return
    def line_changed(self):
        checked_lines = []
        lines = self.get_lines()
        for line in lines:
            checked_lines.append(line["current_line"].isChecked())
        last_clicked = self.sender()

        for line in lines:
            line["current_line"].setChecked(False)
        last_clicked.setChecked(True)

    def action_changed(self):
        # TODO: change red scan trajectory un-scanned points to light gray

        row = self.sender()
        if row.currentIndex() == 1:
            row.parent().setStyleSheet("background: lavender")
        return
    def update_npts(self, line):
        x_step = eval(self.controls.x_step.text())
        y_step = eval(self.controls.y_step.text())
        x_npts = "-1"
        y_npts = "-1"


        x_width = np.abs(eval(line.__dict__["x_width"].text()))
        y_width = np.abs(eval(line.__dict__["y_width"].text()))
        if x_step < x_width:
            x_npts = np.ceil(x_width/x_step)
            x_width = x_npts*x_step
            line.__dict__["x_points"].setText(str(x_npts))
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
            line.__dict__["x_points"].setText(str(int(x_npts)))
            line.__dict__["y_points"].setText(str(int(y_npts)))
            line.__dict__["x_width"].setText(str(np.round(x_width,3)))
            line.__dict__["y_width"].setText(str(np.round(y_width,2)))

    def get_eta(self):
        #TODO: send command to server to get_eta(scan_params)
        # scan_params = ??
        # eta = self.client.get_eta(scan_params)
        # self.controls.eta.setText(str(timedelta(seconds=sum(eta))))
        return

    def get_lines(self):
        lines = [self.lines_layout.itemAt(i).widget().__dict__ for i in range(self.lines_layout.count())]
        return lines
    def get_params(self):
        line = self.lines_layout.itemAt(0).widget().__dict__
        keys = line.keys()
        params = []
        for key in keys:
            if isinstance(line[key], QtWidgets.QWidget):
                params.append(key)
        return params
    def points_clicked(self):
        if self.controls.x_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        if self.controls.y_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        else:
            lines = self.get_lines()
            for line in lines:
                if line.__dict__["current_line"].isChecked():
                    self.update_npts(line)

    def all_clicked(self):
        if self.controls.x_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        if self.controls.y_step.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            return
        else:
            lines = self.get_lines()
            for line in lines:
                if line["current_line"].isChecked():
                    self.update_npts(line)


    def closeEvent(self, event):
        #do other stuff if necessary, perhaps signal to batch_launcher to gracefully disconnect from PVS or something.
        #signal.emit("closing")
        self.save_session()

    def save_session(self):
        #TODO: send session to host server instead of saving locally.
        pass

    def open_session(self):
        #TODO: lines = self.client.get_session()
        pass
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
        height = 25
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
        self.zero_btn = QtWidgets.QPushButton("Zero")
        self.zero_btn.setFixedWidth(size2)
        self.zero_all_btn = QtWidgets.QPushButton("Zero all")
        self.zero_all_btn.setFixedWidth(size2)
        setup_lbl = QtWidgets.QLabel("PV setup window")
        setup_lbl.setFixedWidth(size3)
        zero_lbl = QtWidgets.QLabel("scan line")
        zero_lbl.setFixedWidth(size3)
        zero_all_lbl = QtWidgets.QLabel("all scans")
        zero_all_lbl.setFixedWidth(size3)

        b1 = QtWidgets.QVBoxLayout()
        b1.addWidget(self.setup_btn)
        b1.addWidget(self.zero_btn)
        b1.addWidget(self.zero_all_btn)
        b2 = QtWidgets.QVBoxLayout()
        b2.addWidget(setup_lbl)
        b2.addWidget(zero_lbl)
        b2.addWidget(zero_all_lbl)
        col2 = QtWidgets.QHBoxLayout()
        col2.addLayout(b1)
        col2.addLayout(b2)

        self.begin_btn = QtWidgets.QPushButton("Begin")
        self.begin_btn.setFixedWidth(size2)
        self.pause_btn = QtWidgets.QPushButton("Pause")
        self.pause_btn.setFixedWidth(size2)
        self.continue_btn = QtWidgets.QPushButton("Resume")
        self.continue_btn.setFixedWidth(size2)
        self.abort_btn = QtWidgets.QPushButton("Abort")
        self.abort_btn.setFixedWidth(size2)

        self.backup_scanrecord_btn = QtWidgets.QPushButton("Backup")
        self.backup_scanrecord_btn.setFixedWidth(size2)
        self.connect_server_btn = QtWidgets.QPushButton("connect/start")
        self.connect_server_btn.setFixedWidth(size2)
        begin_lbl = QtWidgets.QLabel("batch scan")
        begin_lbl.setFixedWidth(size3)
        pause_lbl = QtWidgets.QLabel("batch scan")
        pause_lbl.setFixedWidth(size3)
        continue_lbl = QtWidgets.QLabel("from pause")
        continue_lbl.setFixedWidth(size3)
        abort_lbl = QtWidgets.QLabel("current line")
        abort_lbl.setFixedWidth(size3)

        self.backup_scanrecord_lbl = QtWidgets.QLabel("scan record")
        self.backup_scanrecord_lbl.setFixedWidth(size3)
        self.connect_server_lbl = QtWidgets.QLabel("server")
        self.connect_server_lbl.setFixedWidth(size3)

        c1 = QtWidgets.QVBoxLayout()
        c1.addWidget(self.begin_btn)
        c1.addWidget(self.pause_btn)
        c1.addWidget(self.continue_btn)
        c1.addWidget(self.abort_btn)
        c1.addWidget(self.backup_scanrecord_btn)
        c1.addWidget(self.connect_server_btn)
        c2 = QtWidgets.QVBoxLayout()
        c2.addWidget(begin_lbl)
        c2.addWidget(pause_lbl)
        c2.addWidget(continue_lbl)
        c2.addWidget(abort_lbl)
        c2.addWidget(self.backup_scanrecord_lbl)
        c2.addWidget(self.connect_server_lbl)
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
                item.setStyleSheet("QLabel {background-color: white;" 
                                           "color: black;"
                                           "border-width: 0;"
                                           "border-radius: 3;"
                                           "border-style: solid;"
                                           "border-color: white}")
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


class Line(QtWidgets.QWidget):
    paramsChangedSig = QtCore.pyqtSignal(int)
    addlinesig = QtCore.pyqtSignal()
    deletelinesig = QtCore.pyqtSignal(int)
    duplicatelinesig = QtCore.pyqtSignal(int)
    def __init__(self, scan_id):
        super(Line, self).__init__()
        self.id = scan_id
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


    def contextMenuEvent(self, pos):
            #TODO: if scan status == "done"
            # only show [add, duplicate]

            menu = QtWidgets.QMenu()
            add_line_action = menu.addAction("add line")
            delete_line_action = menu.addAction("delete line")
            duplicate_line_action = menu.addAction("duplicate line")
            action = menu.exec_(self.mapToGlobal(pos.pos()))
            menu.popup(QtGui.QCursor.pos())
            if action == add_line_action:
                self.addlinesig.emit()
            if action == delete_line_action:
                self.deletelinesig.emit(self.id)
            if action == duplicate_line_action:
                self.duplicatelinesig.emit(self.id)

    def setupUi(self):
        size1 = 30
        size2 = 60
        size3 = 220
        size4 = 120
        size5 = 75
        height = 25
        line = QtWidgets.QHBoxLayout()
        self.setStyleSheet("background: white")
        self.current_line = QtWidgets.QRadioButton()
        self.current_line.setFixedSize(size1, height)
        self.scan_type = QtWidgets.QPushButton("step", checkable = True)
        self.scan_type.setFixedSize(size1, height)
        self.scan_type.clicked.connect(self.scan_type_clicked)
        self.scan_geometry = QtWidgets.QPushButton("2D", checkable = True)
        self.scan_geometry.setFixedSize(size1, height)
        self.scan_geometry.clicked.connect(self.scan_geometry_clicked)
        self.detectors = CheckableComboBox()
        actions = ["xspress3","xmap", "eiger", "interferometers"]
        self.detectors.addItems(actions)
        self.detectors.setFixedSize(size4, height)
        self.detectors.check_all()
        self.trajectory = QtWidgets.QComboBox()
        trajectories = ["raster","snake","spiral","lissajous","custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedSize(size5, height)
        self.line_action = QtWidgets.QLabel("queue")
        self.line_action.setFixedSize(size5, height)

        self.dwell_time = QtWidgets.QLineEdit()
        self.dwell_time.setPlaceholderText("dwell")
        self.dwell_time.setFixedSize(size2, height)
        self.x_center = QtWidgets.QLineEdit()
        self.x_center.setPlaceholderText("x center")
        self.x_center.setFixedSize(size2, height)
        self.x_points = QtWidgets.QLineEdit()
        self.x_points.setPlaceholderText("x points")
        self.x_points.setFixedSize(size2, height)
        self.x_width = QtWidgets.QLineEdit()
        self.x_width.setPlaceholderText("x width")
        self.x_width.setFixedSize(size2,height)
        self.y_center = QtWidgets.QLineEdit()
        self.y_center.setPlaceholderText("y center")
        self.y_center.setFixedSize(size2,height)
        self.y_points = QtWidgets.QLineEdit()
        self.y_points.setPlaceholderText("y points")
        self.y_points.setFixedSize(size2,height)
        self.y_width = QtWidgets.QLineEdit()
        self.y_width.setPlaceholderText("y width")
        self.y_width.setFixedSize(size2,height)
        self.r_center = QtWidgets.QLineEdit()
        self.r_center.setPlaceholderText("r center")
        self.r_center.setFixedSize(size2,height)
        self.r_points = QtWidgets.QLineEdit()
        self.r_points.setPlaceholderText("r points")
        self.r_points.setFixedSize(size2,height)
        self.r_width = QtWidgets.QLineEdit()
        self.r_width.setPlaceholderText("r width")
        self.r_width.setFixedSize(size2,height)
        self.comments = QtWidgets.QLineEdit("")
        self.comments.setPlaceholderText("notes:")
        self.comments.setFixedSize(size3,height)
        self.save_message = QtWidgets.QLabel("")
        self.save_message.setText("")
        self.save_message.setFixedSize(size3,height)
        self.start_time = QtWidgets.QLabel("")
        self.start_time.setText("")
        self.start_time.setFixedSize(size4, height)
        self.finish_time = QtWidgets.QLabel("")
        self.finish_time.setText("")
        self.finish_time.setFixedSize(size4, height)
        self.line_eta = QtWidgets.QLabel("00:00:00")
        self.line_eta.setFixedSize(size2,height)


        for key in self.__dict__:
            item = getattr(self,key)
            if key == "trajectory":
                item.currentIndexChanged.connect(self.trajector_changed)

            if isinstance(item, QtWidgets.QLineEdit):
                item.editingFinished.connect(self.validate_params)

            elif isinstance(item, QtWidgets.QComboBox):
                item.currentIndexChanged.connect(self.validate_params)

            if isinstance(item, QtWidgets.QHBoxLayout):
                pass
            if isinstance(item, QtCore.pyqtSignal):
                pass
            elif isinstance(item, QtWidgets.QWidget):
                line.addWidget(item)
            else:
                pass
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
            #TODO: change placeholder txt to match spiral parameters
            self.x_center.setEnabled(True)
            self.x_points.setEnabled(True)
            self.x_width.setEnabled(True)
            self.y_center.setEnabled(False)
            self.y_points.setEnabled(False)
            self.y_width.setEnabled(False)
        elif self.trajectory.currentText() == "lissajous":
            #TODO: change placeholder txt to match lisa parameters
            self.x_center.setEnabled(True)
            self.x_points.setEnabled(True)
            self.x_width.setEnabled(True)
            self.y_center.setEnabled(False)
            self.y_points.setEnabled(False)
            self.y_width.setEnabled(False)
        elif self.trajectory.currentText() == "custom":
            #TODO: change placeholder txt to match lisa parameters
            #TODO: blank out parameter fields.
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

    def spiral_selected(self):
        #TODO: set y_width == None disable y_width
        #TODO: set y_points == None disable y_points
        #TODO: set scan type to "STEP" (currently canno flyscan multi-axis)
        pass

    def lissajous_selected(self):
        #TODO: set y_points == None disable y_points
        #TODO: open lissajous interactive window
        #TODO:  x frequency slider 0-1
        #TODO:  y_frequency slider 0-1
        #TODO: display LINE number from which lissa option was opened from.
        #TODO: if trajectory type changes for line, automatically close window.
        #TODO: return trajectory as [x,y] array, execute as "custom" scan
        pass

    def custom_selected(self):
        #TODO: open table window where user can either manually enter list of x,y coordinates, paster them in, OR
        #TODO: in another tab, open hdf5 file with coordinates, to DRAW over an image to create an enclosed region
        #TODO: then specify [x_points, y_points] and either [raster, or snake] to generarte trajecrory, update table, and update plot
        pass
    def custom_draw(self):
        #TODO: create interactive draw windwo but put it under gui
        #open hdf, linedit showing directory
        #create DATA dropdown that explores hdf5 to simulates file browser
        #create element dropdown that explores hdf5 to simulates file browser (optional, but likely necessary)
        #create COORDINATE dropdown that explores hdf5 to simulates file browser find x,y coordinates
        #apply button updates scan trajectory plot
        #clear drawing button
        pass

    def scan_type_clicked(self):
        button = self.sender()
        if button.isChecked():
            button.setText("fly")
        else:
            button.setText("step")
        # scan_id = button.scan_id()
        # self.validate_params(scan_id)

    def scan_geometry_clicked(self):
        button = self.sender()
        if button.isChecked():
            button.setText("2D")
            self.r_center.setVisible(False)
            self.r_points.setVisible(False)
            self.r_width.setVisible(False)
        else:
            button.setText("3D")
            self.r_center.setVisible(True)
            self.r_points.setVisible(True)
            self.r_width.setVisible(True)

        # scan_id = button.scan_id()
        # self.validate_params(scan_id)
    def validate_params(self):
        #TODO: is_valid = self.client.validate_params(scan_id)
        # if is_valid: color = white
        # else: color = salmon
        # self.paint_line(color)
        pass

    def paint_line(self, color):
        self.setStyleSheet("background: {}".format(color))
        self.setAutoFillBackground(True)
        return

    def motor_limits_valid(self):
        #TODO: current_line = self.get_current_line()
        #TODO: is_valid = self.client.validate_motor_limits(current_line.scan_id)
        # return is_valid
        pass
    def make_pretty(self):
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QtWidgets.QCheckBox):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QtWidgets.QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
                if key == "finish_time" or key == "start_time":
                    item.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    item.setFont(myFont)
                    item.setText("")
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

class CheckableComboBox(QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QtGui.QStandardItemModel(self))
        self.check_all()

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
            # print(item.text() + " was unselected.")
        else:
            item.setCheckState(QtCore.Qt.Checked)
            # print(item.text() + " was selected.")
        self.checked_items()

    def item_checked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == QtCore.Qt.Checked

    def checked_items(self):
        checked_indices = []
        for i in range(self.count()):
            if self.item_checked(i):
                # checkedItems.append(self.model().item(i, 0).text())
                checked_indices.append(i)
        return checked_indices

    def check_selected(self, selected):
        self.uncheck_all()
        for i in selected:
            item = self.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Checked)

    def check_all(self):
        for i in range(self.count()):
            item = self.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Checked)

    def uncheck_all(self):
        for i in range(self.count()):
            item = self.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Unchecked)

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
        self.data_trajectory = self.p1.plot([0,1,2,3],[0,0,0,0], pen=pen, symbol='o', symbolSize=5, symbolBrush="w")
        self.data_line = self.p1.plot([0,1,2,3],[0,1,2,3], pen=pen, symbol='o', symbolSize=5, symbolBrush="b")
        self.image_view = pyqtgraph.ImageItem(axisOrder = "row-major")
        self.p1.setMouseEnabled(x=False, y=False)
        self.vb = self.p1.getViewBox()
        self.vb.setBackgroundColor((255,255,255))
        self.setBackground("w")

    def plott(self, x, y):
        self.data_line.setData(x, y)

    def wheelEvent(self, ev):
        #empty function, but leave it as it overrides some other unwanted functionality.
        pass