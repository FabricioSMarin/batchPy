
import sys, os, json, time, re
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/Users/marinf/anaconda3/envs/py310/plugins" #everytime pyqt updates, something breaks.. need to point to plugins now. 
sys.path.insert(0,"/".join(os.path.realpath(__file__).split("/")[:-2])) #adds parent directory to path so importing from other directories work. 
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QScrollArea, QPushButton, QTableWidgetItem


from trajectories import *
from TableWidgetWithContextMenu import TableWidgetWithContextMenu
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder
from Controls import Controls
from ScanSettings import ScanSettings
from Line import Line
from Stream import Stream 
import threading


class BatchScanGui(QMainWindow):
    def __init__(self, app):
        super(QMainWindow, self).__init__()

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
        sys.stdout = Stream(newText=self.onUpdateText)
        self.show()

    def initUI(self):
        self.controls = Controls()
        self.settings = ScanSettings(self)
        self.settings.open_local_settings()
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
        self.queue_menu = menubar.addMenu(' &queue')
        self.queue_menu.addAction(savequeuelog_action)
        self.queue_menu.addAction(clearqueue_action)

        self.batch_widget = self.make_batch_widget(1)
        self.batch_widget.setMaximumHeight(120)
        self.batch_widget.setMinimumHeight(80)

        self.queue_widget = self.make_queue_widget()

        layout = QVBoxLayout()
        layout.addWidget(self.batch_widget)
        layout.addWidget(self.queue_widget)
        layout.addWidget(self.controls)
        layout.setSpacing(0)

        layout2 = QHBoxLayout()
        layout2.addLayout(layout)
        layout2.setSpacing(0)

        self.setLayout(layout2)
        self.closeAction = QAction(' &close', self)
        self.closeAction.setShortcut(' Ctrl+Q')
        self.closeAction.triggered.connect(sys.exit)
        self.controls.abort_btn.clicked.connect(self.queue_abort)
        self.controls.continue_btn.clicked.connect(self.queue_resume)
        self.controls.pause_btn.clicked.connect(self.queue_pause)
        self.controls.begin_btn.clicked.connect(self.queue_start)
        self.controls.visual_box.model().itemChanged.connect(self.view_option_changed)
        #TODO: define positioners some other way ex: get positioners list upon connecting to qserver

        self.open_local_session() #this just restores the plan setup rows from the previous session in case the gui was accidentally closed
        self.get_positioners()
        self.get_detectors()
        self.update_queue()

        return layout2



    def remove_all_but_first(self,combobox):
        # Get the total number of items in the combo box
        count = combobox.count()
        # Remove items from the last one to the second one
        for i in range(count - 1, 0, -1):
            combobox.removeItem(i)

    def view_option_changed(self): 
        #get current option 
        #if option 1: 
        pass

    def update_detectors(self, detectors):
        try:
            print("updating detector list")
            lines = self.get_lines()
            for line in lines:
                line["detectors"].clear()
                line["detectors"].addItems(detectors)
        except Exception as e: 
            print(e)

    def update_positioners(self, positioners):
        try:
            print("updating positioners list")
            lines = self.get_lines()
            for line in lines:
                line["loop1"].clear()
                line["loop2"].clear()
                line["loop3"].clear()
                line["loop4"].clear()
                line["loop1"].addItems(positioners)
                line["loop2"].addItems(positioners)
                line["loop3"].addItems(positioners)
                line["loop4"].addItems(positioners)
        except Exception as e: 
            print(e)

    def plan_selected(self, plan):
        pass

    def send_to_queue(self):
        pass

    def get_queue(self):
        pass

    def update_queue(self): 
        pass

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
        try:
            cursor = self.controls.message_window.textCursor()
            cursor.insertText(text)
            self.controls.message_window.setTextCursor(cursor)
            self.controls.message_window.ensureCursorVisible()
        except: 
            pass

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

        pass

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
        pass

    def queue_edited(self, packed):

        pass

    def queue_clear(self):
        pass
    
    def queue_item_move(self, idxs):

        pass
    def queue_execute_now(self):
        #executes a chosen plan or set of instructions immediately 
        pass

    def queue_abort(self):

        pass

    def queue_resume(self):

        pass

    def queue_pause(self):
        pass
    
    def queue_start(self):
        pass

    def queue_save(self):
        #TODO: get queue history, parse to csv or something easily readable
        pass
        
    def get_positioners(self):
        pass
            
    def get_detectors(self):
        pass

    def get_history(self):
        pass
    
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
