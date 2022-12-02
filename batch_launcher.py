from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import pyqtSignal

import batch_gui
import batch_backend
import sys
import time
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

        app = QtWidgets.QApplication(sys.argv)
        self.gui = batch_gui.BatchScanGui(app)
        self.gui.closeAction.triggered.connect(sys.exit)
        self.gui.initRecordAction.triggered.connect(self.initialize_record)
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
        self.threading_mode = 1
        self.backend = batch_backend.BatchSetup()
        if self.backend.backend_ready:
            self.backend.init_scan_record()
        # self.connect_backend
        self.start_threads()
        sys.exit(app.exec())

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
    def screenshot_window(self):
        # date = datetime.now()
        # filename = date.strftime('%Y-%m-%d_%H-%M-%S.jpg')
        # app = QApplication(sys.argv)
        # QScreen.grabWindow(app.primaryScreen(),
        # QApplication.desktop().winId()).save(filename, 'png')
        #TODO: toggle savedata message, and start/stop time, then screenshot and save current view.
        pass

    def timer_event(self):
        #TODO might move this to threading class
        #TODO: save session
        # global_eta = self.calculate_global_eta()

        pass

    def scan_settings_changed(self):
        #TODO: check if settings violate motor limits, if all good. calculate ETAs
        #TODO: check motor_limits(), check_velocity_limits()
        #TODO: call clculate_line_eta()
        #TODO: call calculate_global_eta()
        #TODO: if not good, highlight line RED
        pass

    def check_motor_limits(self):
        #TODO: get x_width, x_center, y_center, y_width for line
        #TODO: if ends violate softlimits, highlight that row RED, indicating that that line will not be scanned.
        #TODO: print message
        pass

    def check_motor_velocity_limit(self):
        #TODO: get dwell, x_step, and y_step step for line.
        #TODO: if step/dwell violate maxSpeed, highlight that row RED, indicating that that line will not be scanned.
        #TODO: print message
        pass

    def calculate_global_eta(self):
        eta = []
        line_status = []
        line_action = []
        lines = []
        for key in vars(self.gui):
            if isinstance(vars(self.gui)[key], batch_gui.Line):
                lines.append(vars(vars(self.gui)[key]))

        for i, line in enumerate(lines):
            if line["line_action"].currentText() == "normal":
                eta_str = line["line_eta"].text()
                hrs = int(eta_str.split(":")[0]) * 60 * 60
                min = int(eta_str.split(":")[1]) * 60
                sec = int(eta_str.split(":")[2])
                total_s = sec + min + hrs
                if line["status"] == "scanning":
                    #TODO:  calculate eta for current line
                    if line["scan_type"].text() == "fly":
                        line_eta = (self.backend.Scan1.CPT/self.backend.Scan1.NPTS) * total_s
                    else:
                        line_eta = (self.backend.Fscan1.CPT/self.backend.Fscan1.NPTS) * total_s
                    eta.append(line_eta)
                else:
                    eta.append(total_s)
        self.gui.controls.eta.setText(str(timedelta(seconds=sum(eta))))
        return

    def open_PVconfig(self):
        print("Opening PV config file")
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        file = QtWidgets.QFileDialog.getOpenFileName(directory=current_dir, filter="*.pkl")
        if file[0] == '':
            return
        self.backend.open_settings(file[0])
        #TODO: if no scan in progress, open file dialog
        #TODO if scan in progress, print("NOTE: scan in progress for loded PVs. If beamline PVs are correct settings are correct.
        #TODO: load gui session file
        pass


    def update_plot(self):
        #TODO: get current line
        #x,y = get_trajectory()
        #plot(x,y)
        pass

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
            lines[checked].x_center.setText(str(self.backend.ScanH.P1CP))
            lines[checked].x_points.setText(str(self.backend.ScanH.NPTS))
            lines[checked].x_width.setText(str(self.backend.ScanH.P1WD))
            lines[checked].y_center.setText(str(self.backend.Scan1.P1CP))
            lines[checked].y_points.setText(str(self.backend.Scan1.NPTS))
            lines[checked].y_width.setText(str(self.backend.Scan1.P1WD))

        elif scan_type == "fly":
            lines[checked].x_center.setText(str(self.backend.FscanH.P1CP))
            lines[checked].x_points.setText(str(self.backend.FscanH.NPTS))
            lines[checked].x_width.setText(str(self.backend.FscanH.P1WD))
            lines[checked].y_center.setText(str(self.backend.Fscan1.P1CP))
            lines[checked].y_points.setText(str(self.backend.Fscan1.NPTS))
            lines[checked].y_width.setText(str(self.backend.Fscan1.P1WD))

    def export_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        checked = [line.current_line.isChecked() for line in lines].index(True)
        scan_type = lines[checked].scan_type.text()
        if scan_type == "step":
            #use step scan record inner loop
            self.backend.ScanH.P1CP = lines[checked].x_center.text()
            self.backend.ScanH.NPTS = lines[checked].x_points.text()
            self.backend.ScanH.P1WD = lines[checked].x_width.text()
            self.backend.Scan1.P1CP = lines[checked].y_center.text()
            self.backend.Scan1.NPTS = lines[checked].y_points.text()
            self.backend.Scan1.P1WD = lines[checked].y_width.text()

        elif scan_type == "fly":
            self.backend.FscanH.P1CP = lines[checked].x_center.text()
            self.backend.FscanH.NPTS = lines[checked].x_points.text()
            self.backend.FscanH.P1WD = lines[checked].x_width.text()
            self.backend.Fscan1.P1CP = lines[checked].y_center.text()
            self.backend.Fscan1.NPTS = lines[checked].y_points.text()
            self.backend.Fscan1.P1WD = lines[checked].y_width.text()

    def zero_clicked(self):
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        checked = [line.current_line.isChecked() for line in lines].index(True)
        #use step scan record inner loop
        lines[checked].x_center.setText("0")
        lines[checked].x_points.setText("0")
        lines[checked].x_width.setText("0")
        lines[checked].y_center.setText("0")
        lines[checked].y_points.setText("0")
        lines[checked].y_width.setText("0")

    def zero_all_clicked(self):
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        checked = [line.current_line.isChecked() for line in lines].index(True)
        #use step scan record inner loop
        for line in lines:
            line.x_center.setText("0")
            line.x_points.setText("0")
            line.x_width.setText("0")
            line.y_center.setText("0")
            line.y_points.setText("0")
            line.y_width.setText("0")

    def begin_clicked(self):
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
        scan_type = line.scan_type.text()
        dwell = eval(line.dwell_time.text())
        x_center = eval(line.x_center.text())
        x_npts = eval(line.x_points.text())
        x_width = eval(line.x_width.text())
        y_center = eval(line.y_center.text())
        y_npts = eval(line.y_points.text())
        y_width = eval(line.y_width.text())
        scan = [x_center, y_center, x_width, y_width, x_npts, y_npts, dwell]
        line.status = "scanning"
        self.gui.controls.status_bar.setText("scanning line {}".format(first_line))
        print("running scanline: {}".format(first_line))

        if self.gui.tomoAction.isChecked() and self.tomo_valid(first_line):
            r_center = eval(line.r_center.text())
            r_npts = eval(line.r_points.text())
            r_width = eval(line.r_width.text())
            if self.threading_mode == 1:
                print("h1")
                self.thread3.quit()
                self.thread3.wait()
                self.thread3.params = [r_center, r_npts, r_width, scan, scan_type]
                self.thread3.exit_flag = 0
                self.thread3.start()
            else:
                print("h2")
                self.backend.run_tomo(r_center, r_npts, r_width, scan, scan_type)
                self.line_finished_sig()

        else:
            if self.threading_mode == 1:
                print("h3")
                self.thread3.quit()
                self.thread3.wait()
                self.thread3.params = [scan, scan_type]
                self.thread3.exit_flag = 0
                self.thread3.start()
            else:
                print("h4")
                self.backend.run_scan(scan, scan_type)
                self.line_finished_sig()
        return

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
        lines[current_line].status = "done"
        lines[current_line].line_action.setCurrentIndex(0)
        #TODO: set current line.status to "done"
        line_actions = [line.line_action.currentText() for line in lines]
        if "normal" in line_actions:
            next_line = line_actions.index("normal")
            line = lines[next_line]
            scan_type = line.scan_type.text()
            dwell = eval(line.dwell_time.text())
            x_center = eval(line.x_center.text())
            x_npts = eval(line.x_points.text())
            x_width = eval(line.x_width.text())
            y_center = eval(line.y_center.text())
            y_npts = eval(line.y_points.text())
            y_width = eval(line.y_width.text())
            scan = [x_center, y_center, x_width, y_width, x_npts, y_npts, dwell]

            line.status = "scanning"
            self.gui.controls.status_bar.setText("scanning line {}".format(next_line))
            print("running scanline:  {}".format(next_line))

            if self.gui.tomoAction.isChecked() and self.tomo_valid(next_line):
                r_center = eval(line.r_center.text())
                r_npts = eval(line.r_points.text())
                r_width = eval(line.r_width.text())
                #TODO: have conditional scan variable which determines if is tomo or not based on "scan" length.

                if self.threading_mode == 1:
                    print("l1")
                    self.thread3.quit()
                    self.thread3.wait()
                    self.thread3.params = [r_center, r_npts, r_width, scan, scan_type]
                    self.thread3.exit_flag = 0
                    self.thread3.start()
                else:
                    print("l2")
                    self.backend.run_tomo(r_center,r_npts,r_width,scan,scan_type)
                    self.line_finished_sig()
            else:
                print("l3")
                if self.threading_mode == 1:
                    self.thread3.quit()
                    self.thread3.wait()
                    self.thread3.params = [scan, scan_type]
                    self.thread3.exit_flag = 0
                    self.thread3.start()
                else:
                    print("l4")
                    self.backend.run_scan(scan, scan_type)
                    self.line_finished_sig()

        else:
            self.gui.controls.status_bar.setText("batch finished")
            self.backend.cleanup()
            print("cleaning up")

        return
    def pause_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        self.backend.pause_scan()
        self.gui.controls.status_bar.setText("Scan Paused")
        #TODO: disable some buttons to prevent error states

    def continue_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        self.backend.continue_scan()
        self.gui.controls.status_bar.setText("Continuing scan")

    def abort_line_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        self.backend.abort_scan()
        try:
            self.thread3.exit_flag = 1
        except:
            pass
        self.gui.controls.status_bar.setText("Aborting Line")

    def abort_all_clicked(self):
        if not self.backend.backend_ready:
            print("scan record not connected")
            return
        try:
            self.thread3.exit_flag = 1
        except:
            pass
        self.backend.abort_scan()
        lines = [vars(self.gui)[i] for i in self.gui.line_names]
        for line in lines:
            line.line_action.setCurrentIndex(0)

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
        self.thread3 = myThreads(self, 3, "run_scan")

        self.thread1.saveSig.connect(self.gui.save_session)
        self.thread2.etaSig.connect(self.calculate_global_eta)
        self.thread3.lineFinishSig.connect(self.line_finished_sig)
        self.thread1.start()
        self.thread2.start()

    def stop_thread(self):
        self.thread1.exit_flag=1
        self.thread1.quit()
        self.thread1.wait()
        self.thread2.exit_flag=1
        self.thread2.quit()
        self.thread2.wait()
        pass

class myThreads(QtCore.QThread):
    saveSig = pyqtSignal()
    etaSig = pyqtSignal()
    lineFinishSig = pyqtSignal()
    # pvSig = pyqtSignal()

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
        self.exit_flag = 0

    def run(self):
        print ("Starting " + self.name)
        timer = self.timer
        if self.name == "save countdown":
            self.save_countdown(int(timer))
        if self.name == "eta countdown":
            self.eta_countdown(int(timer))
        elif self.name == "run_scan":
            self.run_scan()
        print("Exiting " + self.name)

    def run_scan(self):
        if len(self.params) == 5:
            r_center = self.params[0]
            r_npts = self.params[1]
            r_width = self.params[2]
            scan = self.params[3]
            scan_type = self.params[4]
            self.parent.backend.run_tomo(r_center, r_npts, r_width, scan, scan_type)
        elif len(self.params) == 2:
            scan = self.params[0]
            scan_type = self.params[1]
            self.parent.backend.run_scan(scan, scan_type)
        else:
            print("invalid param settings")
            self.exit_flag = 1
        while True:
            time.sleep(1)
            #if abort or abort_all
            if self.exit_flag == 1:
                print("aborting scan")
                break
            else:
                if self.parent.backend.done == True:
                    print("line finished")
                    self.lineFinishSig.emit()
                    print("sending signal")

                    break
        return

    def save_countdown(self, t):
        t_original = t
        while t:
            time.sleep(1)
            t -= 1
            if t==0 and self.exit_flag==0:
                self.saveSig.emit()  # update counter
                t=t_original
            if self.exit_flag:
                break
            else:
                pass

    def eta_countdown(self, t):
        t_original = t
        while t:
            time.sleep(1)
            t -= 1
            if t==0 and self.exit_flag==0:
                self.etaSig.emit()   #update counter
                t=t_original
            if self.exit_flag:
                break
            else:
                pass

def main():
    Launcher()

if __name__ == "__main__":
    main()