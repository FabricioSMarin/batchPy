import matplotlib.figure

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except:
    print("pyqt6 not installed, trying pyqt5...")
    # from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph
import os
import pickle
from datetime import datetime, timedelta

#GUI structure:
#   Header()
#   Lines()
#   Controls()
#   ImageView()

class BatchScanGui(QtWidgets.QMainWindow):
    def __init__(self,app):
        super(QtWidgets.QMainWindow, self).__init__()
        self.app = app
        self.session_file = "default_session.pkl"
        self.setWindowTitle("Batch Py V1.0.0")
        #TODO: load gui config file

        self.update_interval = 10
        self.num_lines = 20
        self.show_lines = 5
        self.line_names = []
        for i in range(self.num_lines): #max number of lines
            self.line_names.append("line_{}".format(str(i)))
        for v in self.line_names:
            setattr(self, v, Line())
        self.initUI()
        self.restore_session()
        self.show()

    def initUI(self):
        header = Header()
        self.controls = Controls()

        lineframe = QtWidgets.QFrame()
        tmp_layout = QtWidgets.QVBoxLayout()
        for i in range(self.num_lines):
            tmp_layout.addWidget(self.__dict__[self.line_names[i]])
        lineframe.setLayout(tmp_layout)
        lineframe.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);border-width: 1;border-radius: 3;border-style: solid;border-color: rgb(10, 10, 10)}")
        lineframe.setContentsMargins(0,0,0,0) #left, top,right, bottom

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(lineframe)
        layout.addWidget(self.controls)
        layout.setSpacing(0)
        layout.setContentsMargins(10,5,10,10) #left, top,right, bottom

        self.wid = QtWidgets.QWidget()
        self.setCentralWidget(self.wid)
        self.wid.setLayout(layout)
        self.wid.setStyleSheet("background: white")

        self.line_0.current_line.setChecked(True)

        self.closeAction = QtGui.QAction(' &close (Ctrl+Q)', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        self.openAction = QtGui.QAction(' &open PV config (Ctrl+O)', self)
        self.openAction.setShortcut(' Ctrl+O')
        self.saveAction = QtGui.QAction(' &save session (Ctrl+S)', self)
        self.saveAction.setShortcut(' Ctrl+S')

        self.tomoAction = QtGui.QAction(' tomo view', self, checkable=True)
        self.tomoAction.triggered.connect(self.tomoview_changed)
        self.miscviewAction = QtGui.QAction(' misc view', self, checkable=True)
        self.miscviewAction.triggered.connect(self.miscview_changed)

        show_lines = QtWidgets.QMenu("show N lines", self)
        show_lines.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        ag = QtGui.QActionGroup(show_lines)
        ag.setExclusive(True)
        show_lines_options = self.num_lines//5
        for i in range(1,show_lines_options+1):
            #dynamically create instance variable N_line_N and set it to an action
            setattr(self, "N_line_{}".format(str(i*5)), ag.addAction(QtGui.QAction(str(i*5), show_lines, checkable=True)))
            show_lines.addAction(self.__dict__["N_line_{}".format(i*5)])
            self.__dict__["N_line_{}".format(i*5)].triggered.connect(self.num_lines_changed)
        self.num_lines_changed()

        update_interval = QtWidgets.QMenu("update interval (s)", self)
        update_interval.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        ag2 = QtGui.QActionGroup(update_interval)
        ag2.setExclusive(True)

        for i in range(3):
            #dynamically create instance variable N_line_N and set it to an action
            setattr(self, "interval_{}".format(str(i)), ag2.addAction(QtGui.QAction(str(list([10,30,60])[i]), update_interval, checkable=True)))
            update_interval.addAction(self.__dict__["interval_{}".format(i)])
            self.__dict__["interval_{}".format(i)].triggered.connect(self.update_interval_changed)
        self.update_interval_changed()

        for i in range(self.num_lines):
            self.__dict__["line_{}".format(i)].current_line.clicked.connect(self.line_changed)

        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        menubar.setNativeMenuBar(False)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.closeAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)

        settingsMenu = menubar.addMenu(' &Settings')
        settingsMenu.addMenu(show_lines)
        settingsMenu.addMenu(update_interval)

        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(self.tomoAction)
        viewMenu.addAction(self.miscviewAction)

        self.wid.resize(1200, 800)

    def tomoview_changed(self):
        for line in range(self.num_lines):
            self.__dict__[self.line_names[line]].r_center.setVisible(False)
            self.__dict__[self.line_names[line]].r_points.setVisible(False)
            self.__dict__[self.line_names[line]].r_width.setVisible(False)
        if self.tomoAction.isChecked():
            for line in range(self.show_lines):
                self.__dict__[self.line_names[line]].r_center.setVisible(True)
                self.__dict__[self.line_names[line]].r_points.setVisible(True)
                self.__dict__[self.line_names[line]].r_width.setVisible(True)

    def miscview_changed(self):
        for line in range(self.num_lines):
            self.__dict__[self.line_names[line]].save_message.setVisible(False)
            self.__dict__[self.line_names[line]].start_time.setVisible(False)
            self.__dict__[self.line_names[line]].finish_time.setVisible(False)
        if self.miscviewAction.isChecked():
            for line in range(self.show_lines):
                self.__dict__[self.line_names[line]].save_message.setVisible(True)
                self.__dict__[self.line_names[line]].start_time.setVisible(True)
                self.__dict__[self.line_names[line]].finish_time.setVisible(True)

    def line_changed(self):
        checked_lines = []
        for line in range(self.show_lines):
            checked_lines.append(self.__dict__[self.line_names[line]].current_line.isChecked())
        last_clicked = self.sender()

        for line in range(self.show_lines):
            self.__dict__[self.line_names[line]].current_line.setChecked(False)

        last_clicked.setChecked(True)

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
        return

    def update_interval_changed(self):
        intervals = [10,30,60]
        for i in range(3):
            if self.__dict__["interval_{}".format(i)].isChecked():
                self.update_interval = intervals[i]
                break

        #TODO: udate threading counter
        return

    def closeEvent(self,event):
        #do other stuff if necessary, perhaps signal to batch_launcher to gracefully disconnect from PVS or something.
        #signal.emit("closing")
        self.save_session()

    def save_session(self):
        try:
            print("autosaving session")
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

            #TODO: save csv file as wel for easy access
            # header = ["type", "trajectory", "action", "dwell", "x center", "x points", "x width", "y center", "y points",
            #           "y width", "r center", "r points", "r width", "comments", "eta", "start", "finish"]
            #for i,line in self.gui.lines:
            #if i == self.gui.show_lines
            #break
            #else:
            #settings = [line.scan_type.text(), line.trajectory.currentText(), line.action.currentText(), line.dwell.text(), ...

            # with open(cwd+file, 'wb') as f:
            #save csv header
            #for line in "

        except IOError as e:
            print(e)
            print("cannot autosave upon close")

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
        self.x_step = QtWidgets.QLineEdit("0")
        self.x_step.setFixedWidth(size2)
        self.y_step = QtWidgets.QLineEdit("0")
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
        self.Pause_btn = QtWidgets.QPushButton("Pause")
        self.Pause_btn.setFixedWidth(size2)
        self.Continue_btn = QtWidgets.QPushButton("Continue")
        self.Continue_btn.setFixedWidth(size2)
        self.Abort_btn = QtWidgets.QPushButton("Abort")
        self.Abort_btn.setFixedWidth(size2)
        self.Abort_all_btn = QtWidgets.QPushButton("Abort")
        self.Abort_all_btn.setFixedWidth(size2)
        begin_lbl = QtWidgets.QLabel("begin batch scan")
        begin_lbl.setFixedWidth(size3)
        Pause_lbl = QtWidgets.QLabel("pause batch scan")
        Pause_lbl.setFixedWidth(size3)
        Continue_lbl = QtWidgets.QLabel("resume from pause")
        Continue_lbl.setFixedWidth(size3)
        Abort_lbl = QtWidgets.QLabel("abort line")
        Abort_lbl.setFixedWidth(size3)
        Abort_all_lbl = QtWidgets.QLabel("abort all")
        Abort_all_lbl.setFixedWidth(size3)

        c1 = QtWidgets.QVBoxLayout()
        c1.addWidget(self.begin_btn)
        c1.addWidget(self.Pause_btn)
        c1.addWidget(self.Continue_btn)
        c1.addWidget(self.Abort_btn)
        c1.addWidget(self.Abort_all_btn)
        c2 = QtWidgets.QVBoxLayout()
        c2.addWidget(begin_lbl)
        c2.addWidget(Pause_lbl)
        c2.addWidget(Continue_lbl)
        c2.addWidget(Abort_lbl)
        c2.addWidget(Abort_all_lbl)
        col3 = QtWidgets.QHBoxLayout()
        col3.addLayout(c1)
        col3.addLayout(c2)

        self.message_window = QtWidgets.QTextEdit("message bar")
        self.message_window.setFixedWidth(700)
        self.message_window.setStyleSheet("background: beige; color: black")
        self.message_window.setDisabled(True)

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

        combined = QtWidgets.QVBoxLayout()
        combined.addWidget(controlframe)
        combined.addWidget(self.status_bar)
        combined.addWidget(self.message_window)



        combined2 = QtWidgets.QHBoxLayout()
        combined2.addLayout(combined)
        # try:
            # self.view_box = MplCanvas(self, width=5, height=4, dpi=100)
            # self.view_box.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])
            # combined2.addWidget(self.view_box)
        # except:
        #     self.view_box = ImageView()
        #     combined2.addWidget(self.view_box)

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
                item.setStyleSheet("background: lightgreen;color: black; border-radius: 4")
            elif isinstance(item,QtWidgets.QRadioButton):
                item.setStyleSheet("background: white;color: black; border-radius: 4")
            else:
                pass

        self.setStyleSheet("background: white")
        self.setLayout(combined2)

class Header(QtWidgets.QWidget):
    def __init__(self):
        super(Header, self).__init__()
        self.setupUi()

    def setupUi(self):
        size1 = 30
        size2 = 75
        size3 = 200
        line = QtWidgets.QHBoxLayout()
        self.line = QtWidgets.QLabel("line")
        self.line.setFixedWidth(size1)
        self.scan_type = QtWidgets.QLabel("scan \ntype")
        self.scan_type.setFixedWidth(size1)
        self.trajectory = QtWidgets.QLabel("trajectory")
        self.trajectory.setFixedWidth(size2)
        self.line_action = QtWidgets.QLabel("action")
        self.line_action.setFixedWidth(size2)
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
        self.start_time.setFixedWidth(size2)
        self.start_time.setVisible(False)
        self.finish_time = QtWidgets.QLabel("finish time")
        self.finish_time.setFixedWidth(size2)
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
    def __init__(self):
        super(Line, self).__init__()
        self.setupUi()
        self.make_pretty()
        self.trajectory_arr = []
        self.eta = timedelta(seconds=int(0))

    def setupUi(self):
        size1 = 30
        size2 = 75
        size3 = 200
        line = QtWidgets.QHBoxLayout()
        self.setStyleSheet("background: white")
        self.current_line = QtWidgets.QRadioButton()
        self.current_line.setFixedWidth(size1)
        self.scan_type = QtWidgets.QPushButton("step", checkable = True)
        self.scan_type.setFixedWidth(size1)
        self.trajectory = QtWidgets.QComboBox()
        trajectories = ["raster","snake","spiral","lissajous","custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedWidth(size2)
        self.line_action = QtWidgets.QComboBox()
        actions = ["skip","normal", "pause"]
        self.line_action.addItems(actions)
        self.line_action.setFixedWidth(size2)
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
        self.start_time.setFixedWidth(size2)
        self.start_time.setVisible(False)
        self.finish_time = QtWidgets.QLabel("")
        self.finish_time.setFixedWidth(size2)
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
        self.line_eta = QtWidgets.QLabel("eta: hours-minues-seconds")
        self.line_eta.setFixedWidth(size2)

        for key in self.__dict__:
            item = getattr(self,key)
            if key == "trajectory":
                item.currentIndexChanged.connect(self.trajector_changed)
            if isinstance(item, QtWidgets.QLineEdit):
                item.textChanged.connect(self.validate_params)
                item.returnPressed.connect(self.calculate_line_eta)
            elif isinstance(item,QtWidgets.QPushButton):
                item.clicked.connect(self.scan_type_clicked)
            if isinstance(item, QtWidgets.QHBoxLayout):
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

    def validate_params(self):
        for key in self.__dict__:
            item = getattr(self, key)
            if isinstance(item, QtWidgets.QLineEdit):
                try:
                    if key == "comments":
                        pass
                    else:
                        value = eval(item.text())
                        if value<0:
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

    def make_pretty(self):

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QtWidgets.QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QtWidgets.QComboBox):
                # item.setStyleSheet("background: lightyellow;border: 2px red; color: black")
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QtWidgets.QPushButton):
                item.setStyleSheet("background: lightgreen;color: black; border-radius: 4")
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
            return
        dwell = float(self.dwell_time.text())/1000
        x_points = int(self.x_points.text())
        x_width = float(self.x_width.text())
        y_points = 0
        r_points = 0
        seconds_total = 0
        scan_type = self.scan_type.text()
        trajectory = self.trajectory.currentText()
        if scan_type == "step" or scan_type == "fly":
            y_points = int(eval(self.y_points.text()))
            y_width = int(eval(self.y_width.text()))
        if self.r_center.isVisible():
            r_points = int(eval(self.r_points.text()))
            r_width = int(eval(self.r_width.text()))

        if trajectory == "raster":
            if scan_type == "step":
                overhead = 1.3
            else:
                overhead = 1.15
            width_not_zero = (x_width*y_width>0)*1
            seconds_total = dwell*x_points*y_points*overhead*width_not_zero

        if trajectory == "snake":
            if scan_type == "step":
                overhead = 1.2
            else:
                overhead = 1.1
            width_not_zero = (x_width*y_width>0)*1
            seconds_total = dwell*eval(x_points)*eval(y_points)*overhead*width_not_zero

        if trajectory == "spiral" or trajectory == "lissajous" or trajectory == "custom":
            if scan_type == "step":
                overhead = 1.2
            else:
                overhead = 1.1
            seconds_total = dwell*eval(x_points)*overhead

        if self.r_center.isVisible():
            overhead = 1.1
            seconds_total = seconds_total*r_points*overhead

        hms = str(timedelta(seconds=int(seconds_total)))
        self.line_eta.setText(hms)
        #TODO: calculate and update x&y step size for that line
        return

class ImageView(pyqtgraph.GraphicsLayoutWidget):
    def __init__(self):
        super(ImageView, self).__init__()
        self.initUI()

    def initUI(self):
        self.p1 = self.addPlot(title="current scan")
        self.projView = pyqtgraph.ImageItem(axisOrder = "row-major")
        self.p1.setMouseEnabled(x=False, y=False)
        self.vb = self.p1.getViewBox()
        self.vb.setBackgroundColor((255,255,255))
        self.setBackground("w")

    def wheelEvent(self, ev):
        #empty function, but leave it as it overrides some other unwanted functionality.
        pass