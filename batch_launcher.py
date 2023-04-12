import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
# from PyQt5.QtCore import pyqtSignal
import batch_gui
import batch_backend
import sys
import time
import calendar
import subprocess
import os
from datetime import datetime, timedelta
import pickle

class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)
    def write(self, text):
        self.newText.emit(str(text))

class Launcher(object):
    def __init__(self):

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self.gui = batch_gui.BatchScanGui(self.app)
        self.gui.closeAction.triggered.connect(sys.exit)
        self.gui.initRecordAction.triggered.connect(self.initialize_record)
        self.gui.initPVsAction.triggered.connect(self.connect_pvs)
        self.gui.openAction.triggered.connect(self.open_PVconfig)
        self.gui.controls.setup_btn.clicked.connect(self.setup_clicked)
        self.gui.controls.import_btn.clicked.connect(self.import_clicked)
        self.gui.controls.export_btn.clicked.connect(self.export_clicked)
        self.gui.controls.zero_btn.clicked.connect(self.zero_clicked)
        self.gui.controls.zero_all_btn.clicked.connect(self.zero_all_clicked)
        self.gui.controls.begin_btn.clicked.connect(self.begin_clicked)
        self.gui.controls.pause_btn.clicked.connect(self.pause_clicked)
        self.gui.controls.continue_btn.clicked.connect(self.continue_clicked)
        self.gui.controls.abort_btn.clicked.connect(self.abort_line_clicked)
        self.gui.controls.abort_all_btn.clicked.connect(self.abort_all_clicked)
        self.gui.controls.points.clicked.connect(self.calculate_points_clicked)
        self.gui.controls.points_all.clicked.connect(self.calculate_all_points_clicked)

        sys.stdout = Stream(newText=self.onUpdateText)
        self.backend = batch_backend.BatchSetup()
        self.backend.connect_pvs()
        self.update_motor_limits()
        self.start_threads()
        sys.exit(self.app.exec())

    def onUpdateText(self, text):
        # self.gui.controls.message_window.setText(text)
        cursor = self.gui.controls.message_window.textCursor()
        cursor.insertText(text)
        self.gui.controls.message_window.setTextCursor(cursor)
        self.gui.controls.message_window.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__

    def initialize_record(self):
        self.backend.init_scan_record()
    def connect_pvs(self):
        self.backend.connect_pvs()

    def update_motor_limits(self):
        try:
            x_hlm = self.backend.x_motor.HLM
            x_llm = self.backend.x_motor.LLM
            x_vmax = self.backend.x_motor.VMAX
            x_res = self.backend.x_motor.MRES
            y_hlm = self.backend.y_motor.HLM
            y_llm = self.backend.y_motor.LLM
            y_res = self.backend.y_motor.MRES
            if self.backend.r == "empty":
                r_llm = -1000
                r_hlm = 1000
            else:
                r_llm = self.backend.r_motor.LLM
                r_hlm = self.backend.r_motor.HLM

            lines = [vars(self.gui)[i] for i in self.gui.line_names]
            for line in lines:
                line.x_hlm = x_hlm
                line.x_llm = x_llm
                line.x_vmax = x_vmax
                line.x_res = x_res
                line.y_hlm = y_hlm
                line.y_llm = y_llm
                line.y_res = y_res
                line.r_llm = r_llm
                line.r_hlm = r_hlm
        except Exception as e:
            print(e)
            pass

    def calculate_global_eta(self):
        # TODO: global ETA not working
        eta = []
        line_status = []
        line_action = []
        lines = []
        for key in vars(self.gui):
            if isinstance(vars(self.gui)[key], batch_gui.Line):
                lines.append(vars(vars(self.gui)[key]))

        for i, line in enumerate(lines):
            #TODO Somewhere in here causes the program to crash
            if line["line_action"].currentText() == "normal":
                eta_str = line["line_eta"].text()
                hrs = int(eta_str.split(":")[0]) * 60 * 60
                min = int(eta_str.split(":")[1]) * 60
                sec = int(eta_str.split(":")[2])
                total_s = sec + min + hrs
                if line["line_action"].currentText() == "normal":
                    if line["scan_type"].text() == "step":
                        try:
                            line_eta = (self.backend.Scan1.CPT/self.backend.Scan1.NPTS) * total_s
                        except:
                            line_eta = 0
                            pass

                    else:
                        try:
                            line_eta = (self.backend.Fscan1.CPT/self.backend.Fscan1.NPTS) * total_s
                        except:
                            line_eta = 0
                    eta.append(line_eta)
                else:
                    eta.append(total_s)
        self.gui.controls.eta.setText(str(timedelta(seconds=sum(eta))))
        return

    def open_PVconfig(self):
        if self.gui.active_line != -1:
            print("scan in progress, cannot open PV config right now.")
        else:
            print("Opening PV config file")
            current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
            file = QtWidgets.QFileDialog.getOpenFileName(directory=current_dir, filter="*.pkl")
            if file[0] == '':
                return
            self.backend.open_settings(file[0])

    def update_plot(self):
        try:
            # self.gui.controls.view_box.p1.clear()
            x_pos, y_pos = self.get_scan_progress()
            scan = self.get_scan(self.gui.active_line)
            # scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell, r_center, r_width, r_npts
            idx = y_pos*scan[3]+x_pos
            x_arr,y_arr = self.get_trajectory()
            self.gui.controls.view_box.plott(x_arr[:idx],y_arr[:idx])
            return
        except:
            return

    def set_plot(self):
        try:
            x_arr, y_arr = self.get_trajectory()
            self.gui.controls.view_box.data_trajectory.setData(x_arr, y_arr)
            self.gui.controls.view_box.p1.setXRange(x_arr.min(),x_arr.max())
            self.gui.controls.view_box.p1.setYRange(y_arr.min(),y_arr.max())
        except:
            return
    def get_scan_progress(self):
        try:
            x_pos = self.backend.x_motor.RBV
            start = self.backend.inner.P1SP
            end = self.backend.inner.P1EP
            width = self.backend.inner.P1WD
            points = self.backend.inner.NPTS
            faze = self.backend.inner.FAZE


            if faze == 8:
                current_x_pos = int(points)
            else:
                current_x_pos = int(points*(x_pos - start)/(width))
            current_y_pos = self.backend.outer.CPT
            return current_x_pos, current_y_pos
        except:
            return
    def get_trajectory(self):
        line = [vars(self.gui)[i] for i in self.gui.line_names][self.gui.active_line]
        scan = self.get_scan(self.gui.active_line)
        # scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell, r_center, r_width, r_npts
        try:
            if line.trajectory.currentText() == "raster":
                x_line = np.arange(scan[1] - abs(scan[2])/2, scan[1] + abs(scan[2])/2, abs(scan[2])/scan[3])
                x_coords = np.zeros((scan[6],scan[3]))
                for i in range(scan[6]):
                    x_coords[i] = x_line
                x_coords = np.ndarray.flatten(x_coords)

                y_line = np.arange(scan[4] - abs(scan[5])/2, scan[4] + abs(scan[5])/2, abs(scan[5])/scan[6])
                y_coords = np.zeros((scan[6], scan[3]))
                for i in range(scan[6]):
                    y_coords[i] = np.ones(scan[3])*y_line[i]
                y_coords = np.ndarray.flatten(y_coords)
                return x_coords, y_coords

            elif line.trajectory.currentText() == "snake":
                x_line = np.arange(scan[1] - scan[2] / 2, scan[1] + scan[2] / 2, scan[2] / scan[3])
                x_coords = np.zeros((scan[6], scan[3]))
                for i in range(scan[6]):
                    if i%2 == 1:
                        x_coords[:i] = np.fliplr(x_line)
                    else:
                        x_coords[:i] = x_line
                x_coords = np.ndarray.flatten(x_coords)

                y_line = np.arange(scan[4] - scan[5] / 2, scan[4] + scan[5] / 2, scan[4] / scan[6])
                y_coords = np.zeros((scan[6], scan[3]))
                for i in range(scan[6]):
                    y_coords[:i] = np.ones(scan[3]) * y_line[i]
                y_coords = np.ndarray.flatten(y_coords)
                return x_coords, y_coords
            else:
                return
        except:
            return

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

    def setup_clicked(self):
        cwd = os.path.dirname(os.path.abspath(__file__))+"/"
        subprocess.Popen(["python", "{}batch_settings.py".format(cwd)])

    def import_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        checked = [line.current_line.isChecked() for line in lines].index(True)
        scan_type = lines[checked].scan_type.text()
        if scan_type == "step":
            #use step scan record inner loop
            # lines[checked].x_center.setText(str(self.backend.ScanH.P1CP))
            lines[checked].x_center.setText(str(self.backend.x_motor.VAL))
            lines[checked].x_points.setText(str(self.backend.ScanH.NPTS))
            lines[checked].x_width.setText(str(self.backend.ScanH.P1WD))
            # lines[checked].y_center.setText(str(self.backend.Scan1.P1CP))
            lines[checked].y_center.setText(str(self.backend.y_motor.VAL))
            lines[checked].y_points.setText(str(self.backend.Scan1.NPTS))
            lines[checked].y_width.setText(str(self.backend.Scan1.P1WD))


        elif scan_type == "fly":
            # lines[checked].x_center.setText(str(self.backend.FscanH.P1CP))
            lines[checked].x_center.setText(str(self.backend.x_motor.VAL))
            lines[checked].x_points.setText(str(self.backend.FscanH.NPTS))
            lines[checked].x_width.setText(str(self.backend.FscanH.P1WD))
            # lines[checked].y_center.setText(str(self.backend.Fscan1.P1CP))
            lines[checked].y_center.setText(str(self.backend.y_motor.VAL))
            lines[checked].y_points.setText(str(self.backend.Fscan1.NPTS))
            lines[checked].y_width.setText(str(self.backend.Fscan1.P1WD))

    def export_clicked(self):
        # TODO: export button should move motors to center position in additon to exporting scan params to scan record.

        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        checked = [line.current_line.isChecked() for line in lines].index(True)
        scan_type = lines[checked].scan_type.text()
        if scan_type == "step":
            #use step scan record inner loop
            self.backend.ScanH.P1CP = lines[checked].x_center.text()
            self.backend.x_motor.VAL = lines[checked].x_center.text()
            self.backend.ScanH.NPTS = lines[checked].x_points.text()
            self.backend.ScanH.P1WD = lines[checked].x_width.text()
            self.backend.Scan1.P1CP = lines[checked].y_center.text()
            self.backend.y_motor.VAL = lines[checked].y_center.text()
            self.backend.Scan1.NPTS = lines[checked].y_points.text()
            self.backend.Scan1.P1WD = lines[checked].y_width.text()

        elif scan_type == "fly":
            self.backend.FscanH.P1CP = lines[checked].x_center.text()
            self.backend.x_motor.VAL = lines[checked].x_center.text()
            self.backend.FscanH.NPTS = lines[checked].x_points.text()
            self.backend.FscanH.P1WD = lines[checked].x_width.text()
            self.backend.Fscan1.P1CP = lines[checked].y_center.text()
            self.backend.y_motor.VAL = lines[checked].y_center.text()
            self.backend.Fscan1.NPTS = lines[checked].y_points.text()
            self.backend.Fscan1.P1WD = lines[checked].y_width.text()

    def zero_clicked(self):
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        checked = [line.current_line.isChecked() for line in lines].index(True)
        lines[checked].dwell_time.setText("10")
        lines[checked].x_center.setText("0")
        lines[checked].x_points.setText("0")
        lines[checked].x_width.setText("0")
        lines[checked].y_center.setText("0")
        lines[checked].y_points.setText("0")
        lines[checked].y_width.setText("0")
        lines[checked].r_center.setText("0")
        lines[checked].r_points.setText("0")
        lines[checked].r_width.setText("0")
        lines[checked].save_message.setText("")
        lines[checked].start_time.setText("")
        lines[checked].finish_time.setText("")

    def zero_all_clicked(self):
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        for line in lines:
            line.dwell_time.setText("0")
            line.x_center.setText("0")
            line.x_points.setText("0")
            line.x_width.setText("0")
            line.y_center.setText("0")
            line.y_points.setText("0")
            line.y_width.setText("0")
            line.r_center.setText("0")
            line.r_points.setText("0")
            line.r_width.setText("0")
            line.comments.setText("")
            line.save_message.setText("")
            line.start_time.setText("")
            line.finish_time.setText("")

    def begin_clicked(self):
        if self.gui.active_line != -1:
            # self.gui.controls.begin_btn.setEnabled(False)
            print("batch already started")
            return
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        line_actions = [line.line_action.currentText() for line in lines]
        if "normal" in line_actions:
            first_line = line_actions.index("normal")
        else:
            return
        line = lines[first_line]
        self.gui.active_line = first_line
        format_datetime = self.get_datetime()
        line.start_time.setText(format_datetime)
        line.setStyleSheet("background: yellow")
        line.setAutoFillBackground(True)
        scan = self.get_scan(first_line)
        self.set_plot()
        self.gui.controls.status_bar.setText("scanning line {}".format(first_line))
        print("running scanline: {}".format(first_line))
        self.backend.done = False
        self.thread3 = myThreads(self, 3, "run_scan")
        self.thread3.lineFinishSig.connect(self.line_finished_sig)
        self.thread3.exit_scan = 0
        self.timer_thread = myThreads(self, 4, "timer event")
        self.timer_thread.plotSig.connect(self.update_plot)
        # self.timer_thread.xp3StuckSig.connect(self.stuck_flag)
        # self.timer_thread.struckStuckSig.connect(self.stuck_flag)
        self.timer_thread.exit_flag = 0
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)

        self.timer.start()
        self.timer_thread.start()

        if self.gui.tomoAction.isChecked() and self.tomo_valid(first_line):
            self.thread3.params = scan
        else:
            self.thread3.params = scan[:8]
        self.thread3.start()

        return

    # def stuck_flag(self):
    #     self.line_color(self.gui.active_line, "lightsalmon")

    def get_scan(self, line_idx):
        line = [vars(self.gui)[i] for i in self.gui.line_names][line_idx]
        scan_type = line.scan_type.text()
        dwell = eval(line.dwell_time.text())
        x_center = eval(line.x_center.text())
        x_npts = eval(line.x_points.text())
        x_width = eval(line.x_width.text())
        y_center = eval(line.y_center.text())
        y_npts = eval(line.y_points.text())
        y_width = eval(line.y_width.text())
        r_center = eval(line.r_center.text())
        r_npts = eval(line.r_points.text())
        r_width = eval(line.r_width.text())
        return [scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell, r_center, r_width, r_npts]

    def get_datetime(self):
        now = datetime.now()
        day = now.strftime("%a")
        cal_day = now.day
        month = now.month
        year = now.year
        time = datetime.today().time()
        hour = time.hour
        minute = time.minute
        second = time.second
        formatted = "{} {}-{}-{} {}:{}:{}".format(day, month, cal_day, year, hour, minute, second)
        return formatted

    def tomo_valid(self, line_idx):
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        line = lines[line_idx]
        invalid = 0
        if line.r_center.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        if line.r_points.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        else:
            if int(line.r_points.text()) <= 0:
                invalid = 1
        if line.r_width.styleSheet().split(";")[0].split(":")[1].strip() == "lightcoral":
            invalid = 1
        else:
            if int(line.r_width.text()) <= 0:
                invalid = 1
        if invalid:
            return False
        else:
            return True

    def line_finished_sig(self):
        print("starting next line")
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        try:
            current_line = [line.line_action.currentText() for line in lines].index("normal")
        except:
            print("exception")
            return

        line = lines[current_line]
        line.setStyleSheet("background: white")

        if line.line_action.currentText() == "normal":
            line.line_action.setCurrentIndex(3)
            save_message = self.backend.saveData_message
            line.save_message.setText(save_message)
            format_datetime = self.get_datetime()
            line.finish_time.setText(format_datetime)

        line.setAutoFillBackground(True)
        line_actions = [line.line_action.currentText() for line in lines]
        self.backend.done = False
        if "normal" in line_actions or "pause" in line_actions:

            current_line +=1
            line = lines[current_line]
            self.gui.active_line = current_line
            line.setStyleSheet("background: yellow")
            line.setAutoFillBackground(True)
            scan = self.get_scan(current_line)
        else:
            self.gui.controls.status_bar.setText("batch finished")
            self.gui.active_line = -1
            self.backend.cleanup()
            print("cleaning up")
            return

        if line.line_action.currentText() == "skip" or line.line_action.currentText() == "done":
            # line.save_message.setText("")
            # line.comments.setText("")
            # line.start_time.setText("")
            # line.finish_time.setText("")
            print("skipping line {}".format(current_line))
            #TODO: change this logic so it doesnt change any of the line action
            # line.line_action.setCurrentIndex(1)     #setting line_action to "normal" so in the next iteration it goes to the skipped line, then selects the n+1 index from the skipped line.
            self.line_finished_sig()
            return

        if line.line_action.currentText() == "pause":
            self.gui.controls.status_bar.setText("pausing on line {}".format(current_line))
            self.backend.pause_scan()
            print("pausing on  scanline:  {}".format(current_line))
            format_datetime = self.get_datetime()
            line.start_time.setText(format_datetime)

        if line.line_action.currentText() == "normal":
            self.gui.controls.status_bar.setText("scanning line {}".format(current_line))
            print("running scanline:  {}".format(current_line))
            format_datetime = self.get_datetime()
            line.start_time.setText(format_datetime)


        self.set_plot()
        self.thread3 = myThreads(self, 3, "run_scan")
        self.thread3.lineFinishSig.connect(self.line_finished_sig)
        self.timer_thread = myThreads(self, 4, "timer event")
        self.timer_thread.plotSig.connect(self.update_plot)
        # self.timer_thread.xp3StuckSig.connect(self.stuck_flag)
        # self.timer_thread.struckStuckSig.connect(self.stuck_flag)
        self.timer_thread.exit_flag = 0
        self.timer_thread.start()

        if self.gui.tomoAction.isChecked() and self.tomo_valid(current_line):
            self.thread3.params = scan
        else:
            self.thread3.params = scan[:8]
        self.thread3.start()

        return
    def line_color(self, line_idx, color="white"):
        if color == "red" or color == "white":
            line = [vars(self.gui)[i] for i in self.gui.line_names][line_idx]
            line.setStyleSheet("background: {}".format(color))
            line.setAutoFillBackground(True)
        else:
            return

    def pause_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        paused = self.backend.is_paused()
        if paused:
            print("already paused")
            self.gui.controls.pause_btn.setText("Paused")
            self.gui.controls.pause_btn.setStyleSheet("QPushButton {background: lightgreen;color: red; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            return
        else:
            self.backend.add_wait()
            self.gui.controls.status_bar.setText("Scan Paused")
            self.gui.controls.pause_btn.setText("Paused")
            self.gui.controls.pause_btn.setStyleSheet("QPushButton {background: lightgreen;color: red; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")

    def continue_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        retry = 0
        self.backend.continue_scan()
        self.gui.controls.status_bar.setText("Continuing scan")
        while self.backend.is_paused():
            retry+=1
            self.backend.continue_scan()
            if retry>=5:
                return
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        lines[self.gui.active_line].line_action.setCurrentIndex(1)
        self.gui.controls.pause_btn.setText("Pause")
        self.gui.controls.pause_btn.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")

    def abort_line_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        if self.gui.active_line != -1:
            self.backend.abort_scan()
            self.line_color(self.gui.active_line, color="white")
            saveDate_message = self.backend.saveData_message.split("to")[1]
            self.backend.saveData_message = "Aborted {}".format(saveDate_message)
            lines = [vars(self.gui)[i] for i in self.gui.line_names]
            line = lines[self.gui.active_line]
            line.save_message.setText(self.backend.saveData_message)
        self.gui.controls.status_bar.setText("Aborting Line")
        self.gui.active_line = -1
        self.backend.done = True
        try:
                self.thread3.exit_scan = 1
                self.thread3.quit()
                self.timer_thread.exit_flag = 1
                self.timer.stop()
        except:
            print("error aborting scan, try not pressing abort repeatedly")
            pass
        return

    def abort_all_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        try:
            self.thread3.exit_scan = 1
            self.timer_thread.exit_flag = 1
        except:
            pass
        self.gui.active_line = -1
        self.backend.abort_scan()
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        for line in lines:
            line.line_action.setCurrentIndex(0)
        return

    def calculate_points_clicked(self):
        self.gui.points_clicked()
        return

    def calculate_all_points_clicked(self):
        self.gui.all_clicked()
        return

    def custom_draw(self):
        #TODO: create interactive draw windwo but put it under gui
        #open hdf, linedit showing directory
        #create DATA dropdown that explores hdf5 to simulates file browser
        #create element dropdown that explores hdf5 to simulates file browser (optional, but likely necessary)
        #create COORDINATE dropdown that explores hdf5 to simulates file browser find x,y coordinates
        #apply button updates scan trajectory plot
        #clear drawing button
        pass

    def start_threads(self):
        # Create new threads
        self.thread1 = myThreads(self, 1, "save countdown")
        self.thread1.timer = 60
        self.thread2 = myThreads(self, 2, "eta countdown")
        self.thread2.timer = 10

        self.thread1.saveSig.connect(self.gui.save_session)
        self.thread2.etaSig.connect(self.calculate_global_eta)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)

        self.timer.start()
        self.thread1.start()
        self.thread2.start()

    def stop_thread(self):
        self.timer.stop()
        self.thread1.exit_save=1
        self.thread1.quit()
        self.thread1.wait()
        self.thread2.exit_eta=1
        self.thread2.quit()
        self.thread2.wait()
        pass

class myThreads(QtCore.QThread):
    saveSig = pyqtSignal(name="saveSig")
    etaSig = pyqtSignal(name="etaSig")
    lineFinishSig = pyqtSignal(name="lineFinishedSig")
    lineAbortedSig = pyqtSignal(name="lineAbortedSig")
    # xp3StuckSig = pyqtSignal(name="xp3StuckSig")
    # struckStuckSig = pyqtSignal(name="struckStruckSig")
    plotSig = pyqtSignal(name="plotSig")

    def __init__(self, parent, threadID, name):
        super(myThreads, self).__init__()
        # QtCore.QThread.__init__(self)
        self.parent = parent
        self.threadID = threadID
        self.name = name
        self.scanning = 0
        self.params = None
        self.timer = 10
        # self.pv_dict = pv_dict
        self.exit_scan = 0
        self.exit_flag = 0
        self.exit_save = 0
        self.exit_eta = 0

    def run(self):
        print ("Starting " + self.name)
        timer = self.timer
        if self.name == "save countdown":
            self.save_countdown(int(timer))
        if self.name == "eta countdown":
            self.eta_countdown(int(timer))
        if self.name == "run_scan":
            self.run_scan()
        elif self.name == "timer event":
            self.run_timer_action()

    def run_scan(self):

        if len(self.params) == 10:
            #scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell, r_center, r_width, r_npts
            self.parent.backend.run_tomo(self.params[0],self.params[1],self.params[2],self.params[3],self.params[4],self.params[5],self.params[6],self.params[7],self.params[8],self.params[9],self.params[10])
        elif len(self.params) == 8:
            self.parent.backend.run_scan(self.params[0],self.params[1],self.params[2],self.params[3],self.params[4],self.params[5],self.params[6],self.params[7])
        else:
            print("invalid param settings")
            self.exit_scan = 1
            self.exit_flag = 1
        while True:
            time.sleep(1)
            if self.exit_scan == 1:
                print("aborting scan")
                self.lineAbortedSig.emit()
                break
            elif self.parent.backend.done == True:
                self.lineFinishSig.emit()
                print("line finished")
                break
        return

    def run_timer_action(self):
        while self.exit_flag ==0:
            time.sleep(1)
            # if self.parent.backend.xp3_stuck == True:
            #     self.xp3StuckSig.emit()
            # elif self.parent.backend.struck_stuck == True:
            #     self.struckStuckSig.emit()
            if self.parent.backend.event == True:
                self.plotSig.emit()
            else:
                pass
    def save_countdown(self, t):
        t_original = t
        while t:
            time.sleep(1)
            t -= 1
            if t==0 and self.exit_save==0:
                self.saveSig.emit()  # update counter
                t=t_original
            if self.exit_save:
                break
            else:
                pass

    def eta_countdown(self, t):
        t_original = t
        while t:
            time.sleep(1)
            t -= 1
            if t==0 and self.exit_eta==0:
                self.etaSig.emit()   #update counter
                t=t_original
            if self.exit_eta:
                break
            else:
                pass

def main():
    Launcher()

if __name__ == "__main__":
    main()