
import sys
import os
# os.environ['QT_QPA_PLATFORM'] = ""
# os.environ['QT_DEBUG_PLUGINS'] = "1"

os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/Users/marinf/anaconda3/envs/py310/plugins" #everytime pyqt updates, something breaks.. need to point to plugins now. 
#for X11 forwarding, I needed to start Xquarts, remote in with ssh -Y user@host otherwise the gui hangs
sys.path.insert(0,"/".join(os.path.realpath(__file__).split("/")[:-2])) #adds parent directory to path so importing from other directories work. 
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QFrame, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout 
from PyQt5.QtWidgets import QScrollArea, QRadioButton, QPushButton, QMenu, QComboBox, QCheckBox, QTextEdit, QLCDNumber, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QComboBox, QStyledItemDelegate, QStyle, QStyleOptionButton, QStyleOptionComboBox, QVBoxLayout, QWidget, QListView, QStylePainter

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt, QSize, QPoint, QEvent, QRect
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from bluesky_queueserver_api.zmq import REManagerAPI
import pyqtgraph
from datetime import timedelta
import json
import time
from trajectories import *

#DONE: revise scan_record_plan 
#DONE: figure out the param structure for scan_record plan
#DONE: package parameters for ZMQ communication
#TODO: parse parameters from get_queue and populate the table

#TODO: figure out how to subscribe to PVA position stream
#TODO: figure out how to subscribe to PVA spectra stream

class BatchScanGui(QMainWindow):
    def __init__(self, app):
        super(QMainWindow, self).__init__()
        sys.stdout = Stream(newText=self.onUpdateText)
        self.RM = None
        self.queue = None
        self.app = app
        self.frame = QFrame()
        self.active_line = -1
        self.update_interval = 10
        self.line_ids = []
        self.id_counter = 0
        layout = self.initUI()
        self.frame.setLayout(layout)
        self.setWindowTitle("main window")
        self.setCentralWidget(self.frame)
        self.show()


    def initUI(self):
        self.controls = Controls()
        self.batch_widget = self.make_batch_widget(1)
        self.batch_widget.setMaximumHeight(120)
        self.batch_widget.setMinimumHeight(60)

        self.queue_widget = self.make_queue_widget()
        self.settings = ScanSettings(self)
        self.settings.open_local_settings()
        self.settings.setup.load_session.clicked.connect(self.open_local_session)
        self.settings.setup.qserver.clicked.connect(self.connect2qserver)

        #TODO: get motor limits
        #TODO: get deteector limits
         
        layout = QVBoxLayout()
        layout.addWidget(self.batch_widget)
        layout.addWidget(self.queue_widget)
        layout.addWidget(self.controls)
        layout.setSpacing(0)

        self.setLayout(layout)
        self.closeAction = QAction(' &close', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        self.closeAction.triggered.connect(sys.exit)
        self.controls.setup_btn.clicked.connect(self.settings.show)
        self.controls.setup_btn.clicked.connect(self.settings.openEvent)
        self.controls.abort_btn.clicked.connect(self.abort_clicked)
        self.controls.continue_btn.clicked.connect(self.resume_clicked)
        self.controls.pause_btn.clicked.connect(self.pause_clicked)
        self.controls.begin_btn.clicked.connect(self.begin_clicked)
        self.controls.visual_box.model().itemChanged.connect(self.view_option_changed)

        self.open_local_session()
        self.connect2qserver()
        return layout
    
    def view_option_changed(): 
        #get current option 
        #if option 1: 
        pass

    def connect2qserver(self):
        self.RM = REManagerAPI(zmq_control_addr="tcp://isnpc01.xray.aps.anl.gov:60615", zmq_info_addr="tcp://isnpc01.xray.aps.anl.gov:60625")
        try:
            print("connectint to queue server... ")
            print(self.RM.status(), "\n")
            print(self.update_queue())
        except: 
            print("could not connect to queue server")
            return
        
        # self.queue = self.RM.queue_get()

    def update_queue(self):
        if self.RM is not None:
            self.queue = self.RM.queue_get()
            print(self.queue)
            
            #TODO: parse out parameter and update the table. 
                #clear and re-populate or update each line? 

    def onUpdateText(self, text):
        cursor = self.controls.message_window.textCursor()
        cursor.insertText(text)
        self.controls.message_window.setTextCursor(cursor)
        self.controls.message_window.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__

    def add_line(self):
        self.id_counter = self.id_counter + 1
        self.line_ids.append(self.id_counter)
        line_id = self.line_ids[-1]
        setattr(self, f"line_{line_id}", Line(line_id))
        line = self.__dict__["line_{}".format(line_id)]

        line.setAutoFillBackground(True)
        line.addlinesig.connect(self.add_line)
        line.deletelinesig.connect(self.delete_line)
        line.duplicatelinesig.connect(self.duplicate_line)
        line.duplicatelinesig.connect(self.clear_line)
        line.sendToQueueSig.connect(self.enqueue_line)
        line.trajectoryChangedSig.connect(self.validate_params)
        line.lineditEnterdSig.connect(self.validate_params)
        line.trajectory_changed()
        line.loop_changed()
        self.lines_layout.addWidget(line, alignment=QtCore.Qt.AlignLeft)

    def validate_params(self):
        params = self.sender().pre_validate()
        if params is None: 
            # print("validation step failed")
            return
        print("line validation passed")
        self.sender().line_action.setText("ready")
        #TODO: create trajectory
        if params["trajectory"]=="raster":
            x, y, t = raster(eval(params["dwell_time"]), eval(params["l1_size"]), eval(params["l1_center"]), eval(params["l2_center"]), eval(params["l1_width"]), eval(params["l2_width"]), 2)
            self.set_preview(x,y)

        if params["trajectory"]=="snake":
            x, y, t = snake(eval(params["dwell_time"]), eval(params["l1_size"]), eval(params["l1_center"]), eval(params["l2_center"]), eval(params["l1_width"]), eval(params["l2_width"]))
            self.set_preview(x,y)

        if params["trajectory"]=="spiral":
            x, y, t = spiral(eval(params["dwell_time"]), eval(params["radial_step"]), eval(params["step_size"]), eval(params["l2_center"]), eval(params["l2_center"]), eval(params["diameter"]))
            self.set_preview(x,y)

        if params["trajectory"]=="lissajous":
            x, y = lissajous(eval(params["dwell_time"]), eval(params["step_size"]), eval(params["l1_center"]), eval(params["l2_center"]), eval(params["l1_width"]), eval(params["l2_width"]), eval(params["cycles"]), eval(params["x_freq"]), eval(params["y_freq"]))
            self.set_preview(x,y)

        if params["trajectory"]=="custom":
            pass

    def delete_line(self, line_id):
        line = self.__dict__["line_{}".format(line_id)]
        line.deleteLater()
        self.lines_layout.removeWidget(line)
        delattr(self, "line_{}".format(line_id))
        self.line_ids.remove(line_id)

    def duplicate_line(self, line_id):
        self.add_line()
        params = self.get_scan(line_id)
        self.update_scan_line(params,self.line_ids[-1])
        return

    def enqueue_line(self, line_id):
        line=self.get_line(line_id)
        if line["line_action"].text() == "ready" and self.RM is not None:
            params = self.get_params()
            packed = self.pack_params(params)
            #if 3D scan or greater, use item_add_batch,  else use item_add
            self.RM.item_add(packed)
            print("added to queue")

    def pack_params(self, params):
        #Need to make sure param in params have the same name as params from "get_plan_params"
        scan_generator = self.settings.setup.scan_generator.text()
        if scan_generator == "profile move": 
            package = {"item_type":"plan", "name": "profile_move_isn",  "kwargs":{}}
            packed_params = self.get_plan_params("profile_move_isn")

        elif scan_generator == "scan record": 
            package = {"item_type":"plan", "name": "scan_record_isn",  "kwargs":{}}
            packed_params = self.get_plan_params("scan_record_isn")

        package = None
        return package

    def clear_line(self, line_id):
        line = self.get_line(line_id)
        keys = list(line.keys())
        for key in keys:
            if isinstance(line[key], QLineEdit):
                line[key].setText("")

    def make_batch_widget(self, num_lines):
        batch_widget = QScrollArea()
        scroll_widget = QWidget()
        self.lines_layout = QVBoxLayout()

        for i in range(num_lines):
            self.add_line()
        scroll_widget.setLayout(self.lines_layout)
        scroll_widget.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);border-width: 1;border-radius: 3;border-style: solid;border-color: rgb(10, 10, 10)}")
        scroll_widget.setMaximumWidth(2500)
        batch_widget.setWidget(scroll_widget)
        batch_widget.setWidgetResizable(True)
        return batch_widget

    def make_queue_widget(self):
        line_attributes = list(self.get_lines()[0].keys())[1:]
        header = line_attributes +["scanID",  "start message",  "finish message", "eta"]
        num_rows = 10
        queue_widget = QWidget()
        layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        table_widget = QTableWidget()
        table_widget.setRowCount(num_rows)
        table_widget.setColumnCount(len(header))
        
        # Optional: Add headers (for clarity)
        table_widget.setHorizontalHeaderLabels([item for item in header])
        table_widget.setVerticalHeaderLabels([f'Row {i+1}' for i in range(num_rows)])
        scroll_area.setWidget(table_widget)
        layout.addWidget(scroll_area)
        
        queue_widget.setLayout(layout)
        return queue_widget

    def get_line(self, line_id):
        lines = self.get_lines()
        for line in lines:
            if line["id"] == line_id:
                return line
        return None
    
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

    def update_scan_line(self,scan,line_id):
        line = self.get_line(line_id)
        keys = list(scan.keys())
        for key in keys:
            if key == "detectors":
                line[key].check_selected(scan[key])
            elif key == "trajectory":
                line[key].setCurrentIndex(scan[key])
            else:
                line[key].setText(scan[key])

    def update_plot(self):
        while self.scanning:
            time.sleep(1)
            #get current positions array
            #TODO: get scanID
            #TOOO: get trajectory
            #TODO: get scan_progress
            #TODO: set_plot(trajectory[:scan_progress]
            # self.controls.view_box.plott(x_arr[:idx], y_arr[:idx])
        self.controls.view_box.plott(None, None) #TODO:  figure out how to clear
        return

    def get_scan_progress(self):
        #TODO: self.scan.get_scan_progress(line_id)
        pass

    def paint_widget(self, widget, color):
        widget.setStyleSheet("background: {}".format(color))
        widget.setAutoFillBackground(True)
        return

    def set_preview(self, x_arr, y_arr):
        try:
            # x_arr, y_arr = self.get_trajectory()
            self.controls.view_box.data_trajectory.setData(x_arr, y_arr)
            self.controls.view_box.p1.setXRange(x_arr.min(),x_arr.max())
            self.controls.view_box.p1.setYRange(y_arr.min(),y_arr.max())
        except:
            return

    def queue_edited(self):
        #RM.item_update()
        pass
    
    def queue_item_deleted(self,id):
        # RM.item_remove(id)
        pass
    
    def queue_item_moved(selfm,id, pos):
        #RM.item_move(id, pos)
        pass

    def abort_clicked(self):
        if self.RM is not None: 
            self.RM.re_abort()

    def resume_clicked(self):
        if self.RM is not None: 
            self.RM.re_resume()

    def pause_clicked(self):
        if self.RM is not None: 
            self.RM.re_pause()

    def begin_clicked(self):
        if self.RM is not None: #check if queue empty 
            self.RM.queue_start()

    def get_plans(self):
        if self.RM is not None: 
            plans = self.RM.plans_existing()
            plan_names = list(plans["plans_existing"].keys())
            for name in plan_names:
                print(name)
            return plan_names, plans
        
    def get_plan_params(self, plan_name):
        defaults = {}
        if self.RM is not None:
            plan_names, plans = self.get_plans()
            if plan_name in  plan_names: 
                params = plans["plans_existing"][plan_name]["parameters"]
                param_names = [item["name"] for item in plans["plans_existing"][plan_name]["parameters"]]
                param_defaults =  [item["default"] for item in plans["plans_existing"][plan_name]["parameters"]]
                for i, name in enumerate(param_names): 
                    defaults[name] = param_defaults[i]
        return defaults
                

    def get_devices(self):
        if self.RM is not None: 
            devices = self.RM.devices_existing()
            print(devices)

    def get_history(self):
        if self.RM is not None: 
            history = self.RM.history_get()
            print(history)

    def line_color(self, line_idx, color="white"):
        if color == "red" or color == "white":
            line = [vars(self)[i] for i in self.line_names][line_idx]
            line.setStyleSheet("background: {}".format(color))
            line.setAutoFillBackground(True)
        else:
            return

    def get_eta(self, params):
        # eta = self.scan.get_scan_eta(params)
        pass

    def get_lines(self):
        lines = [self.lines_layout.itemAt(i).widget().__dict__ for i in range(self.lines_layout.count())]
        return lines

    def get_params(self):
        line = self.lines_layout.itemAt(0).widget().__dict__
        keys = list(line.keys())
        params = {}
        for key in keys: 
            if isinstance(line[key], QPushButton):
                params[key] = [line[key].text(), line[key].isChecked()]
            elif isinstance(line[key], ComboBoxWithPlaceholder):
                params[key] = [line[key].get_items(), line[key].checked_indices()]
            elif isinstance(line[key], QLabel):
                params[key] = line[key].text()
            elif isinstance(line[key], QLineEdit):
                params[key] = line[key].text()
            else: 
                params[key] = line[key]
        return params

    def closeEvent(self, event):
        print("closing main window")
        if self.RM is not None: 
            try: 
                self.RM.close()
            except: 
                pass
        self.save_local_session()

    def save_local_session(self):
        session = self.get_session()
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_session.json")
        with open(fname, 'w') as f:
            json.dump(session, f)

    def open_local_session(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_session.json")
        if os.path.exists(fname) and os.path.getsize(fname):
            with open(fname, 'r') as f:
                session = json.load(f)
        else:
            session = self.get_session()
            with open(fname, 'w') as f:
                json.dump(session, f)

        lines = self.get_lines()
        keys = list(lines[0].keys())
        if len(session)>len(lines): 
            new_lines = len(session)-len(lines)
            for line in range(new_lines):
                self.add_line()
        elif len(session)<len(lines): 
            delete_lines = len(lines) - len(session)
            for line in range(delete_lines):
                self.delete_line(self.line_ids[0])

        for i in range(len(lines)):
            line = lines[i]
            for key in keys:
                try: 
                    if isinstance(line[key], QPushButton):
                        line[key].setText(session[i][key][0])
                        line[key].setChecked(session[i][key][1])
                    elif isinstance(line[key], ComboBoxWithPlaceholder):
                        for j in range(line[key].count()-1):
                            line[key].removeItem(1)
                        line[key].addItems(session[i][key][0])
                        line[key].check_selected(session[i][key][1])
                    elif isinstance(line[key], QLabel):
                        line[key].setText(session[i][key])
                    elif isinstance(line[key], QLineEdit):
                        line[key].setText(session[i][key])
                    else: 
                        line[key] = session[i][key]

                except Exception as e: 
                    print(e)

    def get_session(self):
        ''' session is a list of dictionaries, each list item corresponds to a scan line and each '''
        lines = self.get_lines()
        keys = list(lines[0].keys())
        session = []
        for line in lines: 
            params = self.get_params(line)
            session.append(params)
        return session

class Controls(QWidget):
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
        eta_lbl = QLabel("ETA")
        eta_lbl.setFixedWidth(size1)
        self.eta = QLabel("0")
        self.eta.setFixedWidth(size4)
        
        a1 = QHBoxLayout()
        a1.addWidget(eta_lbl)
        a1.addWidget(self.eta)
        a2 = QHBoxLayout()
        a4 = QHBoxLayout()
        col1= QVBoxLayout()
        col1.addLayout(a1)
        col1.addLayout(a2)
        col1.addLayout(a4)
        col1.setContentsMargins(0,10,0,0)
        self.setup_btn = QPushButton("setup")
        self.setup_btn.setFixedWidth(size2)
        setup_lbl = QLabel("PV setup window")
        setup_lbl.setFixedWidth(size3)
        self.begin_btn = QPushButton("Begin")
        self.begin_btn.setFixedWidth(size2)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedWidth(size2)
        self.continue_btn = QPushButton("Resume")
        self.continue_btn.setFixedWidth(size2)
        self.abort_btn = QPushButton("Abort")
        self.abort_btn.setFixedWidth(size2)

        self.visual_box = ComboBoxWithPlaceholder("view option", exclusive=True)
        options = ["trajectory preview","position stream","spectra"]
        self.visual_box.addItems(options)
        self.visual_box.setFixedWidth(size3)
        self.visual_box.check_selected([1])

        c1 = QHBoxLayout()
        c1.addWidget(self.begin_btn)
        c1.addWidget(self.pause_btn)
        c1.addWidget(self.continue_btn)
        c1.addWidget(self.abort_btn)
        c1.addWidget(self.setup_btn)
        c1.addWidget(self.visual_box)
        col3 = QHBoxLayout()
        col3.addLayout(c1)
        self.message_window = QTextEdit("")
        self.message_window.setFixedWidth(700)
        self.message_window.setStyleSheet("background: beige; color: black")
        self.message_window.setReadOnly(True)

        control_layout = QHBoxLayout()
        control_layout.addLayout(col1)
        control_layout.addLayout(col3)
        control_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        controlframe = QFrame()
        controlframe.setLayout(control_layout)
        controlframe.setContentsMargins(0,0,0,0) #left, top,right, bottom
        controlframe.setFixedWidth(700)
        combined = QVBoxLayout()
        combined.addWidget(controlframe)
        combined.addWidget(self.message_window)
        combined2 = QHBoxLayout()
        combined2.addLayout(combined)

        self.view_box = ImageView()
        combined2.addWidget(self.view_box)

        include = list(set(locals())-exclude)
        for key in include:
            item = locals()[key]
            if isinstance(item,QLabel):
                item.setStyleSheet("color: black; border-color: white")

        for key in self.__dict__:
            item = getattr(self,key)

            if isinstance(item,QLabel):
                item.setStyleSheet("QLabel {background-color: white;" 
                                           "color: black;"
                                           "border-width: 0;"
                                           "border-radius: 3;"
                                           "border-style: solid;"
                                           "border-color: white}")

            elif isinstance(item, QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            elif isinstance(item,QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            else:
                pass
        # self.setStyleSheet("background: white")
        self.setLayout(combined2)

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
        actions = ["xspress3", "tetramm", "xmap", "eiger", "interferometers"]
        self.detectors.addItems(actions)
        self.detectors.setFixedSize(size4, height)
        self.detectors.check_all()

        self.trajectory = ComboBoxWithPlaceholder("trajectory", exclusive=True)
        self.trajectory.setToolTip("trajectory")
        trajectories = ["raster","snake","spiral","lissajous","custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedSize(size5, height)
        self.trajectory.check_selected([2])

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

    def pre_validate(self):
        #get all linedit type widgets from line
        
        linedits = {}
        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit):
                linedits[key] = item

        for key in linedits.keys(): #prevalidate parameters before sending to server
            item = linedits[key]
            #check if any are empty
            #TODO: if combobox, get the text of selected item
            if item.isVisible() and item.text() == "" and key !="comments" and key !="sample_name":
                # print(f"{key} parameter is empty")
                return
            
            #check if any are non-numeric value with eval(param.text())
            if item.isVisible() and isinstance(item, QLineEdit) and item.text() != "" and key !="comments" and key !="sample_name":
                try: 
                    eval(item.text())
                except:
                    print("not numeric value")
                    return
            #check if any specific keys are less than or equal to 0:
            if item.isVisible() \
                and key == ("dwell" or "l1_center" or "l1_size" or "l1_width" or  "l2_center" or "l2_size" or "l2_width"  or \
                            "l3_center" or "l3_size" or "l3_width"  or  "l4_center" or "l4_size" or "l4_width"  or "step_size" or \
                            "radial_step" or "radial_step" or "diameter" or "x_freq" or "y_freq") \
                and eval(item) <=0:
                # and key == ("dwell" or "x_step" or "y_step" or "r_step" or "step_size" or "radial_step" or "radial_step" or "diameter" or "x_freq" or "y_freq") \

                print(f"invalid value for {key}")
                return
            
        #if function has not exited by now, then gather the parameters to send a validation request to server
        params = self.get_params()
        return params

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

class ScanSettings(QWidget):
    settings_closed_sig = pyqtSignal()
    connect_server_sig = pyqtSignal()

    def __init__(self, parent):
        super(QWidget, self).__init__()
        self.parent = parent
        self.setObjectName("bathcscan_flysetup_vPy")
        self.setAutoFillBackground(True)
        self.settings_dict = {}
        self.var_dict = {}
        self.r=None
        self.initUI()
        self.make_pretty()

    def initUI(self):

        self.setup = Setup()
        for key in vars(self.setup):
            item = vars(self.setup)[key]
            if isinstance(item,QLineEdit):
                if isinstance(item, QLineEdit):
                    self.var_dict[item.objectName] = item
                    self.settings_dict[item.objectName] = ""
                    item.editingFinished.connect(self.settings_changed)
        self.setup.scan_generator.clicked.connect(self.scan_generator_changed)
        self.setup.qserver.clicked.connect(self.connect_server_clicked)
        wid = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(self.setup)
        wid.setLayout(layout)
        wid.setMinimumSize(300, 500)        # self.show()
        self.scan_generator_changed()
        self.setMinimumSize(300,500)

    def connect_server_clicked(self):
        #TODO urgent: connec to queue server if not already. print something saying if connected or not. 
        #pull queue from qserver, if remote queue  differs from local queue, prompt to A) clear remote queue and upload local queue or B) clear local queue and update with remote queue
        self.connect_server_sig.emit()
        pass

    def settings_changed(self):
        for key in self.settings_dict.keys():
            self.settings_dict[key] = self.var_dict[key].text()

    def openEvent(self):
        print("opening window")
        self.open_local_settings()

    def closeEvent(self, a0, QCloseEvent=None):
        print("closing window")
        self.save_local_settings()

    def make_pretty(self):
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self,key)
            if isinstance(item, QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item,QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")

            elif isinstance(item,QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::pressed {background-color: darkgreen;}")
            # elif isinstance(item,QRadioButton):
            #     item.setStyleSheet("background: white;color: black; border-radius: 4")
            else:
                pass

    def changeButton(self,button):
        if button.isChecked():
            button.setStyleSheet("background-color : lightblue")
            button.setText("True")

        else:
            button.setStyleSheet("background-color : grey")
            button.setText("False")

    def probe_pvs(self):
        #TODO: send request to server to get PV status for all those specified in this window.
        #if active, border = None
        #if not connected, border = red
        #update pv dict
        pass

    def open_local_settings(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_settings.json")
        if os.path.exists(fname) and os.path.getsize(fname):
            with open(fname, 'r') as f:
                settings = json.load(f)
                #get only settings that are in gui, anything else gets discarded 
                identicals = settings.keys() & self.settings_dict.keys()
        else:
            settings = self.settings_dict
            with open(fname, 'w') as f:
                json.dump(settings, f)

        for key in identicals:
            self.settings_dict[key] = settings[key]
            try: #incase local file has more settings that are not in gui
                self.var_dict[key].setText(self.settings_dict[key])
            except: 
                pass

    def save_local_settings(self):
        for key in self.settings_dict.keys():
            self.settings_dict[key] = self.var_dict[key].text()
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_settings.json")

        with open(fname, 'w') as f:
            json.dump(self.settings_dict, f)

    def restoresettings(self):
        settings = self.r.get("settings")
        self.settings_dict = settings
        for key in settings.keys():
            print(key)
        pass

    def scan_generator_changed(self):
        lines = [i for i in list(self.setup.__dict__) if "line_" in i]  #get vars with "line_" in name: 
        for line in lines:
            hbox = self.setup.__dict__[line]
            num_widgets = hbox.count()
            for i in range(num_widgets):
                hbox.itemAt(i).widget().setVisible(True)
        if self.setup.scan_generator.isChecked():
            self.setup.scan_generator.setText("profile move")
            self.setup.busy1.setVisible(False)
            self.setup.busy2.setVisible(False)
            self.setup.busy3.setVisible(False)
            self.setup.busy4.setVisible(False)
            self.setup.delay_calc.setVisible(False)
            self.setup.save_data.setVisible(False)
            self.setup.scan_inner.setVisible(False)
            self.setup.scan_outer.setVisible(False)
            self.setup.busy1_lbl.setVisible(False)
            self.setup.busy2_lbl.setVisible(False)
            self.setup.busy3_lbl.setVisible(False)
            self.setup.busy4_lbl.setVisible(False)
            self.setup.delay_calc_lbl.setVisible(False)
            self.setup.save_data_lbl.setVisible(False)
            self.setup.scan_inner_lbl.setVisible(False)
            self.setup.scan_outer_lbl.setVisible(False)
        else: 
            self.setup.scan_generator.setText("scan record")
            self.setup.profile_move.setVisible(False)
            self.setup.profile_move_lbl.setVisible(False)

class Setup(QWidget):
    def __init__(self):
        super(Setup, self).__init__()
        self.setupUi()

    def setupUi(self):
        box = QVBoxLayout()
        self.scroll_area()
        box.addWidget(self.scroll)
        self.setLayout(box)

        self.scan_generator.setCheckable(True)
        self.scan_generator.setStyleSheet("background-color : grey")
        self.scan_generator.setChecked(False)
        self.scan_generator.setText("scan record")

    def scroll_area(self):
        item_dict = {} #[type(button, file, path, dropdown), descriptions[idx], choices[idx],defaults[idx]]
        item_dict["load_session"] = [["label", "button"], "load local session", None, None]
        item_dict["qserver"] = [["label", "button"], "connect to queue server", None, None]
        item_dict["scan_generator"] = [["label", "button"], "scan record or profile move", None, None]
        item_dict["profile_move"] = [["label","linedit"], "profile move PV prefix", None, ""]

        item_dict["busy1"] = [["label","linedit"], "inner before wait busy record", None, ""]
        item_dict["busy2"] = [["label","linedit"], "inner after wait busy record", None, ""]
        item_dict["busy3"] = [["label","linedit"], "outer before wait busy record", None, ""]
        item_dict["busy4"] = [["label","linedit"], "outer before wait busy record", None, ""]
        item_dict["delay_calc"] = [["label","linedit"], "delay calc record PV to delay sending triggers", None, ""]
        item_dict["save_data"] = [["label","linedit"], "saveData PV, holds current filename", None, ""]
        item_dict["scan_inner"] = [["label","linedit"], "scan record inner loop", None, ""]
        item_dict["scan_outer"] = [["label","linedit"], "scan record outer loop", None, ""]

        item_dict["softgluezynq"] = [["label","linedit"], "softgluezynq PV prefix", None, ""]
        item_dict["xspress3"] = [["label","linedit"], "xspress3 pv prefix",  None, ""]
        item_dict["eiger"] = [["label","linedit"], "eiger  pv prefix", None, ""]
        item_dict["struck"] = [["label","linedit"], "struck pv prefix", None, ""]
        item_dict["xmap"] = [["label","linedit"], "xmap pv prefix", None,""]
        item_dict["tetramm"] = [["label","linedit"], "tetramm pv prefix",  None,""]
        item_dict["meascompctr"] = [["label","linedit"], "meascompctr pv prefix", None,""]
        item_dict["x_motor"] = [["label","linedit"], "x positioner", None, ""]
        item_dict["y_motor"] = [["label","linedit"], "y positioner", None, ""]
        item_dict["r_motor"] = [["label","linedit"], "r positioner", None, ""]

        v_box = self.create_widget(item_dict)
        v_box.setSpacing(0)
        v_box.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()  # Widget that contains the collection of Vertical Box
        self.scroll_widget.setLayout(v_box)
        self.scroll.setWidget(self.scroll_widget)
        return

    def create_widget(self, item_dict):
        widgetsizes = [240, 115, 50]
        height = 25
        v_box = QVBoxLayout()
        for i, key in enumerate(item_dict.keys()):
            widget_items = item_dict[key][0]
            attrs = item_dict[key]
            widgetsize = widgetsizes[len(widget_items) - 1]
            line_num = "line_{}".format(i)
            setattr(self, line_num, QHBoxLayout())
            line = self.__dict__[line_num]

            for widget in widget_items:
                if widget == "label":
                    name = key + "_lbl"
                    display = key.replace("_", " ")
                    setattr(self, name, QLabel(key))
                    object = self.__dict__[name]
                    object.setText(display)
                    object.setFixedWidth(widgetsize)
                    object.setToolTip(attrs[1])
                    line.addWidget(object)

                elif widget == "lcd":
                    name = key + "_lcd"
                    setattr(self, name, QLCDNumber())
                    object = self.__dict__[name]
                    object.setFixedWidth(widgetsize)
                    font = QtGui.QFont()
                    font.setBold(False)
                    object.setFont(font)
                    object.setFrameShape(QFrame.Shape.NoFrame)
                    object.setDigitCount(2)
                    object.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
                    object.setProperty("intValue", 10)
                    line.addWidget(object)

                elif widget == "linedit":
                    setattr(self, key, QLineEdit())
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(attrs[3])
                    object.objectName = key
                    line.addWidget(object)

                elif widget == "button":
                    display = key.replace("_", " ")
                    setattr(self, key, QPushButton(key))
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(display)
                    line.addWidget(object)

                elif widget == "file":
                    setattr(self, key, QPushButton(key))
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(attrs[3])
                    line.addWidget(object)

                elif widget == "combobox":
                    name = key+"_cbbx"
                    setattr(self, name, QComboBox())
                    object = self.__dict__[name]
                    object.setFixedWidth(widgetsize)
                    object.setToolTip(attrs[1])
                    options = attrs[2]
                    default = attrs[3]
                    for option in options:
                        object.addItem(option)
                    idx = options.index(default)
                    object.setCurrentIndex(idx)
                    line.addWidget(object)

            v_box.addLayout(line)
        return v_box

class Stream(QtCore.QObject):
    newText = pyqtSignal(str)
    
    def write(self, text):
        self.newText.emit(str(text))

class CheckBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(CheckBoxDelegate, self).__init__(parent)
        self.combo = parent

    def paint(self, painter, option, index):
        item = index.model().itemFromIndex(index)
        if item.isEnabled():
            # Draw the checkbox
            check_box_style_option = QStyleOptionButton()
            if item.checkState() == Qt.Checked:
                check_box_style_option.state |= QStyle.State_On
            else:
                check_box_style_option.state |= QStyle.State_Off

            check_box_style_option.rect = self.getCheckBoxRect(option)

            QApplication.style().drawControl(QStyle.CE_CheckBox, check_box_style_option, painter)

        # Draw the text
        super(CheckBoxDelegate, self).paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            item = model.itemFromIndex(index)
            if item.isEnabled():
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                    if self.combo.exclusive:
                        for i in range(model.rowCount()):
                            if i != index.row():
                                model.item(i).setCheckState(Qt.Unchecked)
        return super(CheckBoxDelegate, self).editorEvent(event, model, option, index)

    def getCheckBoxRect(self, option):
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QPoint(option.rect.x() + 5, option.rect.y() +
                                 (option.rect.height() - check_box_rect.height()) // 2)
        return QRect(check_box_point, check_box_rect.size())

class ComboBoxWithPlaceholder(QComboBox):
    def __init__(self, placeholder_text, exclusive=False, *args, **kwargs):
        super(ComboBoxWithPlaceholder, self).__init__(*args, **kwargs)
        self.placeholder_text = placeholder_text
        self.exclusive = exclusive
        self.setView(QListView())
        self.setItemDelegate(CheckBoxDelegate(self))
        
        self.addItem(self.placeholder_text)
        self.setCurrentIndex(0)
        self.model().item(0).setEnabled(False)

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        # If no item is selected or all items are unchecked, display placeholder text
        if self.currentIndex() == 0 or all(self.itemData(i, Qt.CheckStateRole) == Qt.Unchecked for i in range(1, self.count())):
            opt.currentText = self.placeholder_text

        painter.drawComplexControl(QStyle.CC_ComboBox, opt)
        painter.drawControl(QStyle.CE_ComboBoxLabel, opt)

    def check_all(self):
        for i in range(1, self.model().rowCount()):
            self.model().item(i).setCheckState(Qt.Checked)

    def uncheck_all(self):
        for i in range(1, self.model().rowCount()):
            self.model().item(i).setCheckState(Qt.Unchecked)

    def item_checked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == QtCore.Qt.Checked
    
    def check_selected(self, selected):
        self.uncheck_all()
        for i in selected:
            item = self.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Checked)
    def checked_indices(self):
        checked_indices = []
        for i in range(self.count()):
            if self.item_checked(i):
                # checkedItems.append(self.model().item(i, 0).text())
                checked_indices.append(i)
        return checked_indices
    def checked_names(self):
        checked_items = []
        for i in range(1, self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())
        return checked_items
    
    def get_items(self): 
        items = []
        for i in range(1, self.model().rowCount()):
            items.append(self.model().item(i).text())
        return items
            
class ImageView(pyqtgraph.GraphicsLayoutWidget):
    def __init__(self):
        super(ImageView, self).__init__()
        self.initUI()

    def initUI(self):
        self.p1 = self.addPlot()
        styles = {'color': 'r', 'font-size': '20px'}
        self.p1.setLabel('left', 'Y-pos', **styles)
        self.p1.setLabel('bottom', 'X-pos', **styles)
        # self.p1.setTitle("scan trajectory", color="b", size="20pt")

        self.p1.x = [0,0,0,0]
        self.p1.y = [0,0,0,0]
        pen = pyqtgraph.mkPen(color="k")
        # self.p1.setXRange(0, 10, padding=0)
        # self.p1.setYRange(0,10, padding=0)
        self.data_trajectory = self.p1.plot([0,1,2,3],[0,0,0,0], pen=pen, symbol='o', symbolSize=5, symbolBrush="k")
        # self.data_line = self.p1.plot([0,1,2,3],[0,1,2,3], pen=pen, symbol='o', symbolSize=5, symbolBrush="b")
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWindow = BatchScanGui(app)
    mainWindow.show()
    sys.exit(app.exec())
