from PyQt6 import QtCore, QtGui, QtWidgets
import batch_gui
import sys
import numpy as np

class Launcher(object):
    def __init__(self):
        # batch_gui.main()
        app = QtWidgets.QApplication(sys.argv)
        self.gui = batch_gui.BatchScanGui(app)
        self.gui.closeAction.triggered.connect(sys.exit)
        self.gui.openAction.triggered.connect(self.open_session)
        self.gui.saveAction.triggered.connect(self.save_session)
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
        pass



    def line_param_changed(self):

        global_eta = self.calculate_global_eta()
        return



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

    def calculate_line_eta(self):
        #TODO: line_number, scan type, dwell, npts
        #TODO: update line_eta
        pass

    def calculate_global_eta(self):
        #TODO: current scan eta + not-yet-scanned etas that are not marked "skip"
        #TODO: update globl ETA
        pass

    def open_session(self):
        print("testing")
        #TODO: if no scan in progress, open file dialog
        #TODO: load gui session file
        pass

    def save_session(self):
        #TODO: save show_line number
        #TODO: for each scan line: save, radio, trajectory, action, dwell, xcenter .. etc
        #TODO: xstep ystep
        #TODO: maybe save plot
        #TODO: save log
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

def main():
    Launcher()

if __name__ == "__main__":
    main()