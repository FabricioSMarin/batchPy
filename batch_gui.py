
import sys, os, json, time, re
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/Users/marinf/anaconda3/envs/py310/plugins" #everytime pyqt updates, something breaks.. need to point to plugins now. 
sys.path.insert(0,"/".join(os.path.realpath(__file__).split("/")[:-2])) #adds parent directory to path so importing from other directories work. 
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QFrame, QVBoxLayout, QLabel, QLineEdit, QScrollArea, QPushButton, QTableWidgetItem
from bluesky_queueserver_api.zmq import REManagerAPI
from bluesky_queueserver_api import BPlan, BItem, BInst, BFunc

from trajectories import *
from TableWidgetWithContextMenu import TableWidgetWithContextMenu
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder
from Controls import Controls
from ScanSettings import ScanSettings
from Line import Line
from Stream import Stream 

#DONE: revise scan_record_plan 
#DONE: figure out the param structure for scan_record plan
#DONE: package parameters for ZMQ communication
#DONE: parse parameters from get_queue and populate the table
#DONE: fix line prevalidation
#DONE: implement Pause
#DONE: implement Resume
#DONE: implement Abort
#DONE: implement Start/Begin
#DONE: implement queue clear
#DONE: implement queue_item move
#TOOD: implement get devices
#TOOD: implement get positioners
#DONE: implement queue_item Delete 
#DONE: implement queitem update 

#TODO: figure out how to subscribe to PVA position stream
#TODO: figure out how to subscribe to PVA spectra stream
#TODO: add queue history to the table 
#TODO: Hide inactive header items
#TODO: add pre-configured scan options; specify positioners, step/fly, 
#TODO: set rules for valid trajectories for fly/step scans 
#TODO: locally cache scanned items up to some number for quick visualization 
#TODO  alternatively click-to-open scanned lines to pop up a processed image map of a scan or just the roi sum. 
#TODO: implement console_monitor callback function for when queitem changed and call update quueu list
#TODO: implenent save--> history and current queue as csv 
#TODO: impleemnt save--> log
#TODO: implement pi_directory autosave and autoload 
#TODO: get motor limits
#TODO: get deteector limits

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
        savelog_action = QAction('save terminal log', self)
        savelog_action.triggered.connect(self.save_log)
        savequeuelog_action = QAction('save queue log', self)
        savequeuelog_action.triggered.connect(self.queue_save)
        clearqueue_action = QAction('request clear queue', self)
        clearqueue_action.triggered.connect(self.queue_clear)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.file_menu = menubar.addMenu(' &File')
        self.file_menu.addAction(savelog_action)
        # self.file_menu.addAction(savequeuelog_action)
        self.settings_menu = menubar.addMenu(' &settings')
        # self.settings_menu.addAction(openH5Action)
        self.queue_menu = menubar.addMenu(' &queue')
        self.queue_menu.addAction(savequeuelog_action)
        self.queue_menu.addAction(clearqueue_action)

        self.controls = Controls()
        self.batch_widget = self.make_batch_widget(1)
        self.batch_widget.setMaximumHeight(120)
        self.batch_widget.setMinimumHeight(80)

        self.queue_widget = self.make_queue_widget()
        # self.settings = ScanSettings(self)
        # self.settings.open_local_settings()

        
        layout = QVBoxLayout()
        layout.addWidget(self.batch_widget)
        layout.addWidget(self.queue_widget)
        layout.addWidget(self.controls)
        layout.setSpacing(0)

        self.setLayout(layout)
        self.closeAction = QAction(' &close', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        self.closeAction.triggered.connect(sys.exit)
        # self.controls.setup_btn.clicked.connect(self.settings.show)
        # self.controls.setup_btn.clicked.connect(self.settings.openEvent)
        self.controls.abort_btn.clicked.connect(self.queue_abort)
        self.controls.continue_btn.clicked.connect(self.queue_resume)
        self.controls.pause_btn.clicked.connect(self.queue_pause)
        self.controls.begin_btn.clicked.connect(self.queue_start)
        self.controls.visual_box.model().itemChanged.connect(self.view_option_changed)

        # self.settings.setup.load_session.clicked.connect(self.open_local_session)
        # self.settings.setup.qserver.clicked.connect(self.connect2qserver)
        #TODO: define positioners some other way ex: from iconfig file

        self.open_local_session()
        self.connect2qserver()
        return layout

    def remove_all_but_first(self,combobox):
        # Get the total number of items in the combo box
        count = combobox.count()
        # Remove items from the last one to the second one
        for i in range(count - 1, 0, -1):
            combobox.removeItem(i)

    def view_option_changed(): 
        #get current option 
        #if option 1: 
        pass

    def connect2qserver(self):
        # self.RM = REManagerAPI(zmq_control_addr="tcp://isnpc01.xray.aps.anl.gov:60615", zmq_info_addr="tcp://isnpc01.xray.aps.anl.gov:60625")
        self.RM = REManagerAPI(zmq_control_addr="tcp://localhost:60615", zmq_info_addr="tcp://localhost:60625")
        try:
            print("connectint to queue server... ")
            print(self.RM.status(), "\n")
            self.update_queue()
        except: 
            print("could not connect to queue server")
            return
        
        self.update_queue()

    def update_queue(self):
        if self.RM is not None:
            self.queue = self.RM.queue_get()
        if not self.queue["success"]:
            print("could not retreive queue")
            return
        queue_items = self.queue["items"]
        running_item = self.queue["running_item"]
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        for item in queue_items:
            #maybe display these additional items for each plan 
            user = item["user"]
            item_uid = item["item_uid"]
            params = item["kwargs"]
            params["user"] = user
            params["item_uid"] = item_uid
            self.populate_next_available_row(self.table_widget,params)
            
    def populate_next_available_row(self, table_widget, data_dict):
        # Find the next available row (first empty row)
        next_row = table_widget.rowCount()
        table_widget.insertRow(next_row)

        # Get the header labels from the table widget
        header_labels = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]

        # Populate the row with values from the dictionary
        for key, value in data_dict.items():
            if key in header_labels:
                column_index = header_labels.index(key)
                table_widget.setItem(next_row, column_index, QTableWidgetItem(str(value)))
            else:
                print(f"Warning: Key '{key}' not found in table headers.")

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
        line = self.get_line(self.sender().id)
        preval = self.pre_validate(line)
        if preval is None: 
            print("validation step failed")
            line["line_action"].setText("not ready")
            self.set_preview([0,1], [0,0])
            return
        print("line validation passed")
        line["line_action"].setText("ready")
        params = self.get_params(line)
        trajectory  = params["trajectory"][0][params["trajectory"][1][0]-1]
        if trajectory=="raster":
            x, y, t = raster(eval(params["dwell_time"]), eval(params["l1_size"]), eval(params["l1_center"]), eval(params["l2_center"]), eval(params["l1_width"]), eval(params["l2_width"]), 2)
            self.set_preview(x,y)

        if trajectory=="snake":
            x, y, t = snake(eval(params["dwell_time"]), eval(params["l1_size"]), eval(params["l1_center"]), eval(params["l2_center"]), eval(params["l1_width"]), eval(params["l2_width"]))
            self.set_preview(x,y)

        if trajectory=="spiral":
            x, y, t = spiral(eval(params["dwell_time"]), eval(params["radial_step"]), eval(params["step_size"]), eval(params["l2_center"]), eval(params["l2_center"]), eval(params["diameter"]))
            self.set_preview(x,y)

        if trajectory=="lissajous":
            x, y = lissajous(eval(params["dwell_time"]), eval(params["step_size"]), eval(params["l1_center"]), eval(params["l2_center"]), eval(params["l1_width"]), eval(params["l2_width"]), eval(params["cycles"]), eval(params["x_freq"]), eval(params["y_freq"]))
            self.set_preview(x,y)

        if trajectory=="custom":
            pass

    def pre_validate(self, line):
        #prevalidate parameters before sending to server
        # get all linedits from line        
        linedits = {}
        keys = list(line.keys())
        for key in keys:
            if isinstance(line[key], QLineEdit):
                linedits[key] = line[key]
        #check if anylinedit is empty (except for comments)
        for key in linedits.keys(): 
            item = linedits[key]
            if item.isVisible() and item.text() == "" and key !="comments":
                return
            
            #check if any are non-numeric value with eval(param.text())
            if item.isVisible() and item.text() != "" and key !="comments" and key !="sample_name":
                try: 
                    eval(item.text())
                except:
                    print("not numeric value")
                    return
            #check if any specific keys are less than or equal to 0:
            if key == ("dwell_time" or "l1_size" or "l1_width"  or "l2_size" or "l2_width"  or \
                            "l3_size" or "l3_width" or "l4_size" or "l4_width"  or "step_size" or \
                            "radial_step" or "diameter" or "x_freq" or "y_freq") and eval(item.text()) <=0:
                print(f"invalid value for {key}")
                return
            if key == ("l1_center" or "l2_center" or "l3_center" or "l4_center"):
                #not sure if there are any invalid numeric values for center parameters
                pass
            if key == "sample_name" and bool(re.search(r'[^\w\s]', item.text())):
                print("sample name must not contain special characters other than _")
                return
                 
        #if function has not exited by now, then gather the parameters to send a validation request to server
        params = self.get_params()
        return params

    def delete_line(self, line_id):
        line = self.__dict__["line_{}".format(line_id)]
        line.deleteLater()
        self.lines_layout.removeWidget(line)
        delattr(self, "line_{}".format(line_id))
        self.line_ids.remove(line_id)

    def duplicate_line(self, line_id):
        self.add_line()
        line = self.get_line(line_id)
        params = self.get_params(line)
        self.update_scan_line(params,self.line_ids[-1])
        return

    def enqueue_line(self, line_id):
        line=self.get_line(line_id)
        if line["line_action"].text() == "ready" and self.RM is not None:
            try:
                params = self.get_params()
                params["pi_directory"] = self.controls.pi_dir.text()
                packed = self.pack_params(params)
                #if 3D scan or greater, use item_add_batch,  else use item_add
                self.RM.item_add(packed)
                print("added to queue")
            except: 
                print("could not add to queue")
                return
        self.update_queue()

    def enqueue_line_test(self, line_id):
        line=self.get_line(line_id)
        if line["line_action"].text() == "ready" and self.RM is not None:
            try:
                params = self.get_params()
                params["pi_directory"] = self.controls.pi_dir.text()
                packed = self.pack_params(params)
                #if 3D scan or greater, use item_add_batch,  else use item_add
                self.RM.item_add(packed)
                print("added to queue")
            except: 
                print("could not add to queue")
                return
        self.update_queue()

        
    def pack_params(self, params):
        #NOTE: need to make sure param in params have the same name as params from "get_plan_params"
        # scan_generator = self.settings.setup.scan_generator.text()
        #TODO: replace this ^
        scan_generator = "scan record"
        params["scan_type"] = params["scan_type"][0]
        params["devices"] = [params["devices"][0][i-1] for i in params["devices"][1]] #-1 because placeholder text item does not count
        params["trajectory"] = params["trajectory"][0][params["trajectory"][1][0]]
        params["loop1"] = params["loop1"][0][params["loop1"][1][0]-1] if len(params["loop1"][1])==1 else ""
        params["loop2"] = params["loop2"][0][params["loop2"][1][0]-1] if len(params["loop2"][1])==1 else ""
        params["loop3"] = params["loop3"][0][params["loop3"][1][0]-1] if len(params["loop3"][1])==1 else ""
        params["loop4"] = params["loop4"][0][params["loop4"][1][0]-1] if len(params["loop4"][1])==1 else ""
        if scan_generator == "profile move": 
            package = {"item_type":"plan", "name": "profile_move_isn",  "kwargs":None}
            packed_params, param_names = self.get_plan_params("profile_move_isn")

        elif scan_generator == "scan record": 
            package = {"item_type":"plan", "name": "scan_record_isn",  "kwargs":None}
            # package = {"item_type":"plan", "name": "test_plan",  "kwargs":{"timer":20, "is_paused":False}}
            packed_params, param_names = self.get_plan_params("scan_record_isn")
            # return package
        for param in param_names:
            if param in params: 
                packed_params[param] = params[param]
            else: 
                print(f"{param} not in plan defaults, skipping...")
        package["kwargs"] = packed_params
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
        header = line_attributes +["item_uid",  "user", "start message",  "finish message", "eta"]
        num_rows = 0
        queue_widget = QWidget()
        layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.table_widget = TableWidgetWithContextMenu()
        self.table_widget.setRowCount(num_rows)
        self.table_widget.setColumnCount(len(header))
        self.table_widget.deleteRowSig.connect(self.queue_delete_item)
        self.table_widget.moveRowSig.connect(self.queue_item_move)
        self.table_widget.editedSig.connect(self.queue_edited)
        
        # Optional: Add headers (for clarity)
        self.table_widget.setHorizontalHeaderLabels([item for item in header])
        self.table_widget.setVerticalHeaderLabels([f'Row {i+1}' for i in range(num_rows)])
        scroll_area.setWidget(self.table_widget)
        layout.addWidget(scroll_area)
        
        queue_widget.setLayout(layout)
        return queue_widget

    def get_line(self, line_id):
        lines = self.get_lines()
        for line in lines:
            if line["id"] == line_id:
                return line
        return None

    def update_scan_line(self,params,line_id):
        line = self.get_line(line_id)
        keys = list(line.keys())
        for key in keys:
            try: 
                if isinstance(line[key], QPushButton):
                    line[key].setText(params[key][0])
                    line[key].setChecked(params[key][1])
                elif isinstance(line[key], ComboBoxWithPlaceholder):
                    for j in range(line[key].count()-1):
                        line[key].removeItem(1)
                    line[key].addItems(params[key][0])
                    line[key].check_selected(params[key][1])
                elif isinstance(line[key], QLabel):
                    line[key].setText(params[key])
                elif isinstance(line[key], QLineEdit):
                    line[key].setText(params[key])
                else: 
                    pass
            except Exception as e: 
                print(e)

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

    def queue_delete_item(self, row_index):
        if self.RM is not None: 
            try: 
                uid = self.table_widget.get_cell_content(row_index, "item_uid")
                self.RM.item_remove(uid=uid)
                self.table_widget.removeRow(row_index)
            except Exception as e: 
                print(e)

    def queue_edited(self, packed):
        if self.RM is not None: 
            try: 
                row, key, new_value = packed[0], packed[1], packed[2]
                uid = self.table_widget.get_cell_content(row, "item_uid")
                response = self.RM.item_get(uid=uid)
                item = BItem(response["item"])
                item.kwargs[key] = new_value
                self.RM.item_update(item)      
                self.update_queue()
  
            except Exception as e: 
                print(e)

    def queue_clear(self):
        if self.RM is not None: 
            self.RM.clear()
    
    def queue_item_move(self, idxs):
        if self.RM is not None: 
            print(f"moving row from pos {idxs[0]} to pos {idxs[1]}")
            # self.RM.item_move(uid="uid-source", before_uid="uid-dest")
            self.RM.item_move(pos=idxs[0], pos_dest=idxs[1])
            self.update_queue()

    def queue_execute_now(self):
        #executes a chosen plan or set of instructions immediately 
        pass

    def queue_abort(self):
        if self.RM is not None: 
            try: 
                self.RM.function_execute(BFunc("abort_scan"), run_in_background=True, user_group="root")
                print("abort request sent")
            except Exception as e: 
                print(e)

    def queue_resume(self):
        if self.RM is not None: 
            try: 
                self.RM.function_execute(BFunc("resume_scan"), run_in_background=True, user_group="root")
                print("resume request sent")
            except Exception as e: 
                print(e)

    def queue_pause(self):
        if self.RM is not None: 
            try: 
                self.RM.function_execute(BFunc("pause_scan"), run_in_background=True, user_group="root")
                print("pause request sent")
            except Exception as e: 
                print(e)
                
    def queue_start(self):
        if self.RM is not None: #check if queue empty 
            self.RM.queue_start()

    def queue_save(self):
        #TODO: get queue history, parse to csv or something easily readable
        pass

    def bs_script_upload(self):
        # scrit = """def pause_queue():\n\t    import epics; epics.caput("hometst:m1", 1)\n pause_queue()\n"""
        # self.RM.script_upload(scrit, run_in_background=True)
        pass

    def get_plans(self):
        if self.RM is not None: 
            plans = self.RM.plans_existing()
            plan_names = [plan for plan in plans["plans_existing"]]
            return plan_names, plans
        
    def get_plan_params(self, plan_name):
        defaults = {}
        
        if self.RM is not None:
            plan_names, plans = self.get_plans()
            if plan_name in plan_names: 
                params = plans["plans_existing"][plan_name]["parameters"]
                param_names = [param["name"] for param in params]
                param_defaults =  [param["default"] for param in params]
                for i, param in enumerate(param_names): 
                    defaults[param] = param_defaults[i]
        return defaults, param_names

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

    def get_params(self, line=None):
        if line is None:
            line = self.lines_layout.itemAt(0).widget().__dict__
        keys = list(line.keys())
        params = {}
        for key in keys: 
            if isinstance(line[key], QPushButton):
                params[key] = [line[key].text(), line[key].isChecked()]
            elif isinstance(line[key], ComboBoxWithPlaceholder):
                items = line[key].get_items()
                indices = line[key].checked_indices()
                params[key] = [items, indices]
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

    def save_log(self): 
        pass

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWindow = BatchScanGui(app)
    mainWindow.show()
    sys.exit(app.exec())
