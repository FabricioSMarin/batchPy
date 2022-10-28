from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import pyqtSignal

import batch_gui
import sys
import time


class Launcher(object):
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        self.gui = batch_gui.BatchScanGui(app)
        self.gui.closeAction.triggered.connect(sys.exit)
        self.gui.openAction.triggered.connect(self.open_PVconfig)

        # self.start_threads()
        sys.exit(app.exec())


    def screenshot_window(self):
        # date = datetime.now()
        # filename = date.strftime('%Y-%m-%d_%H-%M-%S.jpg')
        # app = QApplication(sys.argv)
        # QScreen.grabWindow(app.primaryScreen(),
        # QApplication.desktop().winId()).save(filename, 'png')
        #TODO: toggle savedata message, and start/stop time, then screenshot and save current view.
        pass

    def timer_event(self):
        #TODO: save session, update ETA
        #TODO: other stuff?
        #TODO: might move this to Threading class
        global_eta = self.calculate_global_eta()

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
        # eta = []
        # lines = []
        # for key in vars(self.gui):
        #     if isinstance(vars(self.gui)[key], self.gui.Line):
        #         lines.append(vars(vars(self.gui)[key]))
        #
        # for i, line in enumerate(lines):
        #     eta = line.eta
        #     action = line.action.currentIndex()


            #if line<current_line: eta = 0
            #if skip: eta = 0
            #if current scan: eta - scanned
            #
        #TODO: current scan eta + not-yet-scanned etas that are not marked "skip"
        #TODO: update globl ETA
        pass

    def open_PVconfig(self):
        print("Opening PV config file")

        #TODO: if no scan in progress, open file dialog
        #TODO if scan in progress, print("NOTE: scan in progress for loded PVs. If beamline PVs are correct settings are correct.
        #TODO: load gui session file
        pass


    def update_plot(self):
        #TODO: get current line
        #x,y = get_trajectory()
        #plot(x,y)
        pass

    def snake_selected(self):
        pass

    def raster_selected(self):
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
        pass

    def import_cliked(self):
        pass

    def export_clicked(self):
        pass

    def zero_clicked(self):
        pass

    def zero_all_clicked(self):
        pass

    def begin_clikced(self):
        pass

    def pause_clicked(self):
        pass

    def continue_clicked(self):
        pass

    def abort_line_clicked(self):
        pass

    def abort_all_clicked(self):
        pass

    def calculate_points_clicked(self):
        pass

    def calculate_all_points_clicked(self):
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

    def start_threads(self):
        # Create new threads
        # self.thread1 = myThreads(1, "countdown",self.pv_dict)
        self.thread1 = myThreads(1, "autosave countdown")
        self.thread1.timer = 30
        self.thread2 = myThreads(2, "eta countdown")
        self.thread2.timer = 10

        self.thread1.countSig.connect(self.gui.save_session)
        self.thread2.countSig.connect(self.calculate_global_eta)
        self.thread1.start()
        self.thread2.start()
        print("test")
    def stop_thread(self):
        self.thread1.exit_flag=1
        self.thread1.quit()
        self.thread1.wait()
        self.thread2.exit_flag=1
        self.thread2.quit()
        self.thread2.wait()

class myThreads(QtCore.QThread):
    countSig = pyqtSignal()
    # pvSig = pyqtSignal()

    def __init__(self, threadID, name):
        QtCore.QThread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.timer = 10
        # self.pv_dict = pv_dict
        self.exit_flag = 0

    def run(self):
        print ("Starting " + self.name)
        timer = self.timer
        if self.name == "countdown":
            self.countdown(int(timer))
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
                self.countSig.emit()   #update counter

def main():
    Launcher()

if __name__ == "__main__":
    main()