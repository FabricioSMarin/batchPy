from PyQt5 import QtGui
from PyQt5.QtWidgets import  QWidget, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMenu, QComboBox, QCheckBox
from PyQt5.QtCore import pyqtSignal
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder

class Line(QWidget):
    sendToQueueSig = pyqtSignal(int)
    trajectoryChangedSig = pyqtSignal()
    lineditEnterdSig = pyqtSignal()
    paramsChangedSig = pyqtSignal(int)
    addlinesig = pyqtSignal()
    deletelinesig = pyqtSignal(int)
    duplicatelinesig = pyqtSignal(int)

    def __init__(self, line_id):
        super(Line, self).__init__()
        self.id = line_id
        self.setupUi()
        self.make_pretty()

    def contextMenuEvent(self, pos):
            #TODO: if scan status == "done"
            # only show [add, duplicate]

            menu = QMenu()
            enqueue_line_action = menu.addAction("add to queue")
            add_line_action = menu.addAction("add line")
            delete_line_action = menu.addAction("delete line")
            duplicate_line_action = menu.addAction("duplicate line")
            clear_line_action = menu.addAction("clear line")

            action = menu.exec_(self.mapToGlobal(pos.pos()))
            menu.popup(QtGui.QCursor.pos())
            if action == enqueue_line_action: 
                self.sendToQueueSig.emit(self.id)
            if action == add_line_action:
                self.addlinesig.emit()
            if action == delete_line_action:
                self.deletelinesig.emit(self.id)
            if action == duplicate_line_action:
                self.duplicatelinesig.emit(self.id)
            if action == clear_line_action:
                self.clearlinesig.emit(self.id)
                
    def setupUi(self):
        size1 = 30
        size2 = 100
        size3 = 220
        size4 = 120
        size5 = 75
        height = 25
        line = QHBoxLayout()
        self.setStyleSheet("background: white")

        self.scan_type = QPushButton("step", checkable = True)
        self.scan_type.setToolTip("scan_type")
        self.scan_type.setFixedSize(size1, height)
        self.scan_type.clicked.connect(self.scan_type_changed)

        self.detectors = ComboBoxWithPlaceholder("detectors")
        self.detectors.setToolTip("detectors")
        detectors = ["xspress3", "tetramm", "xmap", "eiger", "interferometers"]
        self.detectors.addItems(detectors)
        self.detectors.setFixedSize(size4, height)
        self.detectors.check_all()

        self.trajectory = ComboBoxWithPlaceholder("trajectory", exclusive=True)
        self.trajectory.setToolTip("trajectory")
        trajectories = ["raster","snake","spiral","lissajous","custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedSize(size5, height)
        self.trajectory.check_selected([2])

        #TODO: get axis options from settings
        axis_options = ["motor 1","motor 2","motor 3", "temperature","energy",'voltage']
        self.loop1 = ComboBoxWithPlaceholder("loop1", exclusive=True)
        self.loop1.setToolTip("loop1")
        self.loop2 = ComboBoxWithPlaceholder("loop2", exclusive=True)
        self.loop2.setToolTip("loop2")
        self.loop3 = ComboBoxWithPlaceholder("loop3", exclusive=True)
        self.loop3.setToolTip("loop3")
        self.loop4 = ComboBoxWithPlaceholder("loop4", exclusive=True)
        self.loop4.setToolTip("loop4")
        self.loop1.addItems(axis_options[:3])
        self.loop1.setFixedSize(size5, height)
        self.loop1.check_selected([1])
        self.loop1.model().itemChanged.connect(self.loop_changed)
        self.loop2.addItems(axis_options)
        self.loop2.setFixedSize(size5, height)
        self.loop2.check_selected([2])
        self.loop2.model().itemChanged.connect(self.loop_changed)
        self.loop3.addItems(axis_options)
        self.loop3.setFixedSize(size5, height)
        self.loop3.model().itemChanged.connect(self.loop_changed)
        self.loop4.addItems(axis_options)
        self.loop4.setFixedSize(size5, height)
        self.loop4.model().itemChanged.connect(self.loop_changed)
        self.line_action = QLabel("not ready")
        self.line_action.setFixedSize(size5, height)
        self.line_action.setToolTip("line_action")
        self.sample_name = QLineEdit()
        self.sample_name.setToolTip("sample_name")
        self.sample_name.setPlaceholderText("sample name")
        self.sample_name.setFixedSize(size2, height) 
        self.dwell_time = QLineEdit()
        self.dwell_time.setToolTip("dwell_time")
        self.dwell_time.setPlaceholderText("dwell time (ms)")
        self.dwell_time.setFixedSize(size2, height) 
        self.l1_center = QLineEdit()
        self.l1_center.setToolTip("l1_center")
        self.l1_center.setPlaceholderText("center 1")
        self.l1_center.setFixedSize(size2, height)
        self.l1_size = QLineEdit()
        self.l1_size.setToolTip("l1_size")
        self.l1_size.setPlaceholderText("step size 1")
        self.l1_size.editingFinished.connect(self.update_width)
        self.l1_size.setFixedSize(size2, height)
        self.l1_size.editingFinished.connect(self.update_width)
        self.l1_width = QLineEdit()
        self.l1_width.setToolTip("l1_width")
        self.l1_width.setPlaceholderText("width 1")
        self.l1_width.setFixedSize(size2,height)
        self.l2_center = QLineEdit()
        self.l2_center.setToolTip("l2_center")
        self.l2_center.setPlaceholderText("center 2")
        self.l2_center.setFixedSize(size2,height)
        self.l2_size = QLineEdit()
        self.l2_size.setToolTip("l2_size")
        self.l2_size.setPlaceholderText("step size 2")
        self.l2_size.setFixedSize(size2,height)
        self.l2_size.editingFinished.connect(self.update_width)
        self.l2_width = QLineEdit()
        self.l2_width.setToolTip("l2_width")
        self.l2_width.setPlaceholderText("width 2")
        self.l2_width.editingFinished.connect(self.update_width)
        self.l2_width.setFixedSize(size2,height)
        self.l3_center = QLineEdit()
        self.l3_center.setToolTip("l3_center")
        self.l3_center.setPlaceholderText("center 3")
        self.l3_center.setFixedSize(size2, height)
        self.l3_size = QLineEdit()
        self.l3_size.setToolTip("l3_size")
        self.l3_size.setPlaceholderText("step size 3")
        self.l3_size.editingFinished.connect(self.update_width)
        self.l3_size.setFixedSize(size2, height)
        self.l3_width = QLineEdit()
        self.l3_width.setToolTip("l3_width")
        self.l3_width.setPlaceholderText("width 3")
        self.l3_width.setFixedSize(size2,height)
        self.l3_size.editingFinished.connect(self.update_width)
        self.l4_center = QLineEdit()
        self.l4_center.setToolTip("l4_center")
        self.l4_center.setPlaceholderText("center 4")
        self.l4_center.setFixedSize(size2, height)
        self.l4_size = QLineEdit()
        self.l4_size.setToolTip("l4_size")
        self.l4_size.setPlaceholderText("step size 4")
        self.l4_size.editingFinished.connect(self.update_width)
        self.l4_size.setFixedSize(size2, height)
        self.l4_width = QLineEdit()
        self.l4_width.setToolTip("l4_width")
        self.l4_width.setPlaceholderText("width 4")
        self.l4_width.setFixedSize(size2,height)
        self.l4_size.editingFinished.connect(self.update_width)
        self.step_size = QLineEdit()
        self.step_size.setToolTip("step_size")
        self.step_size.setPlaceholderText("step size")
        self.step_size.setFixedSize(size2, height)
        self.radial_step = QLineEdit()
        self.radial_step.setToolTip("radial_step")
        self.radial_step.setPlaceholderText("radial step size")
        self.radial_step.setFixedSize(size2, height)
        self.diameter = QLineEdit()
        self.diameter.setToolTip("diameter")
        self.diameter.setPlaceholderText("diameter")
        self.diameter.setFixedSize(size2, height)
        self.cycles = QLineEdit()
        self.cycles.setToolTip("cycles")
        self.cycles.setPlaceholderText("# cycles")
        self.cycles.setFixedSize(size2, height)  
        self.x_freq = QLineEdit()
        self.x_freq.setToolTip("x_freq")
        self.x_freq.setPlaceholderText("x frequency")
        self.x_freq.setFixedSize(size2, height)      
        self.y_freq = QLineEdit()
        self.y_freq.setToolTip("y_freq")
        self.y_freq.setPlaceholderText("y frequency")
        self.y_freq.setFixedSize(size2, height)           
        self.comments = QLineEdit("")
        self.comments.setToolTip("comments")
        self.comments.setPlaceholderText("notes:")
        self.comments.setFixedSize(size3,height)
        self.trajectory.model().itemChanged.connect(self.trajectory_changed)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit) and key != "comments":
                item.returnPressed.connect(self.line_changed)
                pass
            if isinstance(item, QWidget): 
                line.addWidget(item)
        line.setContentsMargins(0,0,0,0)
        self.setLayout(line)

    def line_changed(self):
        self.lineditEnterdSig.emit()

    def loop_changed(self):
        loop1 = self.loop1.checked_names()
        loop2 = self.loop2.checked_names()
        loop3 = self.loop3.checked_names()
        loop4 = self.loop4.checked_names()

        if len(loop1)==0:
            self.l1_center.setVisible(False)
            self.l1_size.setVisible(False)
            self.l1_width.setVisible(False)
        else: 
            self.l1_center.setVisible(True)
            self.l1_size.setVisible(True)
            self.l1_width.setVisible(True)

        if len(loop2)==0:
            self.l2_center.setVisible(False)
            self.l2_size.setVisible(False)
            self.l2_width.setVisible(False)
        else: 
            self.l2_center.setVisible(True)
            self.l2_size.setVisible(True)
            self.l2_width.setVisible(True)
        pass

        if len(loop3)==0:
            self.l3_center.setVisible(False)
            self.l3_size.setVisible(False)
            self.l3_width.setVisible(False)
        else: 
            self.l3_center.setVisible(True)
            self.l3_size.setVisible(True)
            self.l3_width.setVisible(True)

        if len(loop4)==0:
            self.l4_center.setVisible(False)
            self.l4_size.setVisible(False)
            self.l4_width.setVisible(False)
        else: 
            self.l4_center.setVisible(True)
            self.l4_size.setVisible(True)
            self.l4_width.setVisible(True)


    def trajectory_changed(self):
        current_trajectory = self.trajectory.checked_names()[0]
        if current_trajectory == "raster" or current_trajectory == "snake":
            self.dwell_time.setVisible(True)
            self.step_size.setVisible(False)
            self.radial_step.setVisible(False)
            self.diameter.setVisible(False)
            self.x_freq.setVisible(False)
            self.y_freq.setVisible(False)
            self.cycles.setVisible(False)

        elif current_trajectory == "spiral":
            self.dwell_time.setVisible(True)
            self.step_size.setVisible(True)
            self.radial_step.setVisible(True)
            self.diameter.setVisible(True)
            self.x_freq.setVisible(False)
            self.y_freq.setVisible(False)
            self.cycles.setVisible(False)

        elif current_trajectory == "lissajous":
            self.dwell_time.setVisible(True)
            self.step_size.setVisible(True)
            self.radial_step.setVisible(False)
            self.diameter.setVisible(False)
            self.x_freq.setVisible(True)
            self.y_freq.setVisible(True)
            self.cycles.setVisible(True)

        elif current_trajectory == "custom":
            self.dwell_time.setVisible(False)
            self.step_size.setVisible(False)
            self.radial_step.setVisible(False)
            self.diameter.setVisible(False)
            self.x_freq.setVisible(False)
            self.y_freq.setVisible(False)
            self.cycles.setVisible(False)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit):
                if item.isEnabled():
                    item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
                else:
                    item.setStyleSheet("background: lightblue; color: lightblue; border-radius: 4")


    def custom_draw(self):
        #TODO: create interactive draw windwo but put it under gui
        #open hdf, linedit showing directory
        #create DATA dropdown that explores hdf5 to simulates file browser
        #create element dropdown that explores hdf5 to simulates file browser (optional, but likely necessary)
        #create COORDINATE dropdown that explores hdf5 to simulates file browser find x,y coordinates
        #apply button updates scan trajectory plot
        #clear drawing button
        pass

    def update_width(self):
        #TODO: change number of points to step size and adjust width based on step size, ceil to narest step-size multiple
        #TODO:
        pass

    def get_params(self):
        #get all linedit type widgets from line
        params = {}
        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit) or isinstance(item, QPushButton) or isinstance(item, QLabel):
                params[key] = item.text()
        #TODO: for detectors, get the ones that are checked only or add second list with "is_enabled" mask
        params["detectors"] = self.detectors.checked_names()
        params["trajectory"] = self.trajectory.checked_names()[0]
        return params
    
    def set_params(self, params):
        pass

    def scan_type_changed(self):
        if self.scan_type.isChecked():
            self.scan_type.setText("fly")
        else:
            self.scan_type.setText("step")

    def motor_limits_valid(self):
        #TODO: current_line = self.get_current_line()
        #TODO: is_valid = self.client.validate_motor_limits(current_line.line_id)
        # return is_valid
        pass

    def make_pretty(self):
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QCheckBox):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item,QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::checked {background-color: orchid;}")
            else:
                pass
        return
