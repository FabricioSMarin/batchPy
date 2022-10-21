import matplotlib.figure

try:
    from PyQt6 import QtCore, QtGui, QtWidgets, Qt
except:
    print("pyqt6 not installed, trying pyqt5...")
    from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

class BatchScanGui(QtWidgets.QMainWindow):
    def __init__(self,app):
        super(QtWidgets.QMainWindow, self).__init__()
        self.app = app
        self.setWindowTitle("Batch Py V1.0.0")
        #TODO: load gui config file

        self.update_interval = 10
        self.num_lines = 10
        self.show_lines = 5
        self.line_names = []
        for i in range(self.num_lines): #max number of lines
            self.line_names.append("line_{}".format(str(i)))
        for v in self.line_names:
            setattr(self, v, Line())
        self.initUI()

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

        wid = QtWidgets.QWidget()
        self.setCentralWidget(wid)
        wid.setLayout(layout)
        wid.setStyleSheet("background: white")
        self.show()

        #view >> toggle tomography view
        #view >>  parameter log window


        #check motor limit violation


        self.closeAction = QtGui.QAction(' &close', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        self.openAction = QtGui.QAction(' &open config', self)
        self.openAction.setShortcut(' Ctrl+O')
        self.saveAction = QtGui.QAction(' &save config', self)
        self.saveAction.setShortcut(' Ctrl+S')

        show_lines = QtWidgets.QMenu("show N lines", self)
        show_lines.setStyleSheet("background-color: rgb(49,49,49); color: rgb(255,255,255); border: 1px solid #000;")
        ag = QtGui.QActionGroup(show_lines)
        ag.setExclusive(True)
        for i in range(self.num_lines):
            #dynamically create instance variable N_line_N and set it to an action
            setattr(self, "N_line_{}".format(str(i)), ag.addAction(QtGui.QAction(str(i), show_lines, checkable=True)))
            show_lines.addAction(self.__dict__["N_line_{}".format(i)])
            self.__dict__["N_line_{}".format(i)].triggered.connect(self.num_lines_changed)
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

    def num_lines_changed(self):
        for i in range(self.num_lines):
            if self.__dict__["N_line_{}".format(i)].isChecked():
                self.show_lines = i
                break
        for i in range(self.num_lines):
            self.__dict__[self.line_names[i]].setVisible(False)
        for i in range(self.show_lines):
            self.__dict__[self.line_names[i]].setVisible(True)
        #TODO: if currently selected line is > number available lines. set the active line to the last available line

    def update_interval_changed(self):
        intervals = [10,30,60]
        for i in range(3):
            if self.__dict__["interval_{}".format(i)].isChecked():
                self.update_interval = intervals[i]
                break

        #TODO: udate threading counter
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

        exlude = set(locals())
        eta_lbl = QtWidgets.QLabel("ETA")
        eta_lbl.setFixedWidth(size1)
        self.eta = QtWidgets.QLabel("Hours min seconds")
        self.eta.setFixedWidth(size4)
        self.points = QtWidgets.QPushButton("pts")
        self.points.setFixedWidth(size1)
        self.points_all = QtWidgets.QPushButton("all")
        self.points_all.setFixedWidth(size1)
        self.x_step = QtWidgets.QLineEdit("xstep")
        self.x_step.setFixedWidth(size2)
        self.y_step = QtWidgets.QLineEdit("xstep")
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

        self.messge_window = QtWidgets.QTextEdit("message bar")
        self.messge_window.setFixedWidth(700)
        self.messge_window.setStyleSheet("background: beige; color: black")
        self.messge_window.setDisabled(True)

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
        combined.addWidget(self.messge_window)

        # self.view_box = ImageView()
        self.view_box = MplCanvas(self, width=5, height=4, dpi=100)
        self.view_box.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])

        combined2 = QtWidgets.QHBoxLayout()
        combined2.addLayout(combined)
        combined2.addWidget(self.view_box)

        include = list(set(locals())-exlude)
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
        self.current_line = QtWidgets.QLabel("line")
        self.current_line.setFixedWidth(size1)
        self.scan_type = QtWidgets.QLabel("scan \ntype")
        self.scan_type.setFixedWidth(size1)
        self.trajectory = QtWidgets.QLabel("trajectory")
        self.trajectory.setFixedWidth(size2)
        self.line_action = QtWidgets.QLabel("action")
        self.line_action.setFixedWidth(size2)
        self.dwell_time = QtWidgets.QLabel("dwell \ntime")
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
        self.global_eta = QtWidgets.QLabel("eta")
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

    def setupUi(self):
        size1 = 30
        size2 = 75
        size3 = 200
        line = QtWidgets.QHBoxLayout()
        self.setStyleSheet("background: white")
        self.current_line = QtWidgets.QRadioButton()
        self.current_line.setFixedWidth(size1)
        self.scan_type = QtWidgets.QPushButton("fly")
        self.scan_type.setFixedWidth(size1)
        self.trajectory = QtWidgets.QComboBox()
        trajectories = ["raster","snake","spiral","lissajous","custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedWidth(size2)
        self.line_action = QtWidgets.QComboBox()
        actions = ["skip","normal", "pause"]
        self.line_action.addItems(actions)
        self.line_action.setFixedWidth(size2)
        self.dwell_time = QtWidgets.QLineEdit("dwell")
        self.dwell_time.setFixedWidth(size1)
        self.x_center = QtWidgets.QLineEdit("x center")
        self.x_center.setFixedWidth(size2)
        self.x_points = QtWidgets.QLineEdit("x points")
        self.x_points.setFixedWidth(size2)
        self.x_width = QtWidgets.QLineEdit("x width")
        self.x_width.setFixedWidth(size2)
        self.y_center = QtWidgets.QLineEdit("y center")
        self.y_center.setFixedWidth(size2)
        self.y_points = QtWidgets.QLineEdit("y points")
        self.y_points.setFixedWidth(size2)
        self.y_width = QtWidgets.QLineEdit("y width")
        self.y_width.setFixedWidth(size2)
        self.comments = QtWidgets.QLineEdit("comments")
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
        self.r_center = QtWidgets.QLineEdit("r center")
        self.r_center.setFixedWidth(size2)
        self.r_center.setVisible(False)
        self.r_points = QtWidgets.QLineEdit("r points")
        self.r_points.setFixedWidth(size2)
        self.r_points.setVisible(False)
        self.r_width = QtWidgets.QLineEdit("r width")
        self.r_width.setFixedWidth(size2)
        self.r_width.setVisible(False)
        self.line_eta = QtWidgets.QLabel("eta: hours-minues-seconds")
        self.line_eta.setFixedWidth(size2)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QtWidgets.QHBoxLayout):
                pass
            else:
                line.addWidget(item)
        line.setContentsMargins(0,0,0,0)
        self.setLayout(line)

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

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        # fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        self.axes.set_title("scan trajectory")
        #self.axes.set_legend() #scanned points, trajectory
        #self.axes.add_image()
        super(MplCanvas, self).__init__(fig)
