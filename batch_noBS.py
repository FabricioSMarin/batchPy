
import sys, os, json, time, re
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/Users/marinf/anaconda3/envs/py310/plugins" #everytime pyqt updates, something breaks.. need to point to plugins now. 
sys.path.insert(0,"/".join(os.path.realpath(__file__).split("/")[:-2])) #adds parent directory to path so importing from other directories work. 
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QScrollArea, QPushButton, QTableWidgetItem, QDialog, QGridLayout, QDialogButtonBox


from trajectories import *
from TableWidgetWithContextMenu import TableWidgetWithContextMenu
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder
from Controls import Controls
from ScanSettings import ScanSettings
from Line import Line
from Stream import Stream 
import threading
import epics


class SettingsManager:
    """Settings manager that provides settings data without UI"""
    def __init__(self, parent=None):
        self.parent = parent
        self.settings_data = {}
        self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "settings.json")
            
            if os.path.exists(fname):
                with open(fname, 'r') as f:
                    self.settings_data = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings_data = {}
    
    def get_setting(self, key):
        """Get a setting value by key"""
        return self.settings_data.get(key, "")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        # Ensure it's a proper standalone window
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint | 
                           QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        
        # Create the main layout
        layout = QVBoxLayout()
        
        # Create grid layout for settings rows
        grid_layout = QGridLayout()
        
        # Create ten rows of QLabel and QLineEdit widgets
        self.settings_widgets = {}
        settings_labels = [
            "Fly Loop 1 PV", "Fly Loop 2 PV", "Fly Loop 3 PV", "Fly Loop 4 PV",
            "Step Loop 1 PV", "Step Loop 2 PV", "Step Loop 3 PV", "Step Loop 4 PV",
            "Positioner 1 PV", "Positioner 1 RBV", "Positioner 2 PV", "Positioner 2 RBV",
            "Positioner 3 PV", "Positioner 3 RBV", "Positioner 4 PV", "Positioner 4 RBV",
            "saveData mount point", "host mount point", "Det 1 mount point", "Det 1 filePath PV", 
            "Det 2 mount point", "Det 2 filePath PV", "Det 3 mount point", "Det 3 filePath PV",
            "Det 4 mount point", "Det 4 filePath PV", "Det 5 mount point", "Det 5 filePath PV",
            "Det 6 mount point", "Det 6 filePath PV", "PI Directory"
        ]
        
        for i, label_text in enumerate(settings_labels):
            # Create label
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(150)
            
            # Create line edit
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Enter {label_text.lower()}")
            line_edit.setMinimumWidth(200)
            
            # Store reference for later access
            self.settings_widgets[label_text] = line_edit
            
            # Add to grid
            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(line_edit, i, 1)
        
        # Add some spacing
        grid_layout.setSpacing(10)
        grid_layout.setColumnMinimumWidth(0, 150)
        grid_layout.setColumnMinimumWidth(1, 200)
        
        # Add grid to main layout
        layout.addLayout(grid_layout)
        
        # Add button box with OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Load saved settings
        self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "settings.json")
            
            if os.path.exists(fname):
                with open(fname, 'r') as f:
                    settings_data = json.load(f)
                
                # Apply loaded settings to widgets
                for key, value in settings_data.items():
                    if key in self.settings_widgets:
                        self.settings_widgets[key].setText(str(value))
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            settings_data = {}
            for key, widget in self.settings_widgets.items():
                settings_data[key] = widget.text()
            
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "settings.json")
            
            with open(fname, 'w') as f:
                json.dump(settings_data, f, indent=2)
            print(f"Settings saved to {fname}")
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def accept(self):
        """Override accept to save settings before closing"""
        self.save_settings()
        super(SettingsDialog, self).accept()
    
    def get_setting(self, key):
        """Get a setting value by key"""
        if key in self.settings_widgets:
            return self.settings_widgets[key].text()
        return ""


class BatchScanGui(QMainWindow):
    def __init__(self, app):
        super(QMainWindow, self).__init__()

        self.queue = None
        self.app = app
        self.timeout = 1
        self.active_line = -1
        self.update_interval = 10
        self.line_ids = []
        self.id_counter = 0
        
        # Create settings manager (no UI)
        self.settings_manager = SettingsManager(self)
        
        # Create frame first
        self.frame = QFrame()
        
        layout = self.initUI()
        self.frame.setLayout(layout)
        self.setWindowTitle("main window")
        self.setCentralWidget(self.frame)
        sys.stdout = Stream(newText=self.onUpdateText)
        
        # Load saved lines, queue, and PI directory after UI is fully initialized
        self.load_lines_from_json()
        self.load_queue_from_json()
        self.load_pi_dir()
        self.show()

    def initUI(self):
        self.controls = Controls()
        self.settings = ScanSettings(self)
        self.settings.open_local_settings()
        # Settings dialog will be created after UI is fully initialized
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
        
        # Add settings menu
        self.settings_menu = menubar.addMenu(' &Settings')
        settings_action = QAction(' &Open Settings', self)
        settings_action.triggered.connect(self.open_settings)
        self.settings_menu.addAction(settings_action)

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
        return layout2


    def remove_all_but_first(self,combobox):
        # Get the total number of items in the combo box
        count = combobox.count()
        # Remove items from the last one to the second one
        for i in range(count - 1, 0, -1):
            combobox.removeItem(i)

    def view_option_changed(self): 
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

    def send_to_queue(self, params):
        try:
            # Populate the next available row in queue_widget with params
            self.populate_next_available_row(self.table_widget, params)
            print("Added to queue widget")
        except Exception as e:
            print(f"Error adding to queue widget: {e}")
        pass

    def open_settings(self):
        """Open the settings dialog"""
        # Create a new settings dialog instance each time
        settings_dialog = SettingsDialog(self)
        
        # Pre-populate PI Directory from current value
        settings_dialog.settings_widgets["PI Directory"].setText(self.controls.pi_dir.text())
        
        # Ensure it's a proper popup window
        settings_dialog.setWindowFlags(settings_dialog.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        settings_dialog.raise_()
        settings_dialog.activateWindow()
        
        result = settings_dialog.exec_()
        if result == QDialog.Accepted:
            # Update PI directory if changed in settings
            new_pi_dir = settings_dialog.get_setting("PI Directory")
            if new_pi_dir != self.controls.pi_dir.text():
                self.controls.pi_dir.setText(new_pi_dir)
                print(f"PI Directory updated to: {new_pi_dir}")
            print("Settings saved successfully")
        else:
            print("Settings dialog cancelled")


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
        # Use settings manager (no UI) for Line initialization
        setattr(self, f"line_{line_id}", Line(line_id, self.settings_manager))
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
        else: 
            print("pre-line validation passed")
            limits_passed = self.check_limits(preval)
            if limits_passed:
                print("limits passed")
            else:
                print("limits not passed")
                line["line_action"].setText("not ready")
                self.set_preview([0,1], [0,0])
                return

        line["line_action"].setText("ready")
        params = self.get_params(line)
        trajectory  = params["trajectory"][0]
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

    def check_limits(self, params):
        if self.settings_dialog.get_setting("Positioner 1 PV") != "":
            if self.settings_dialog.get_setting("Positioner 1 PV").split(":")[1].split(".")[0][0]=="m":
                try:
                    mvel = epics.caget(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "VMAX", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "VMAX:", mvel)
                except:
                    mvel = None
                    return False
                try:
                    p1egu = epics.caget(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "EGU", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "EGU:", p1egu)
                    S = 0.001 if (p1egu=="um" or p1egu=="micron") else 1
                    T = 0.001 if params["type"]=="fly" else 1
                    scan_vel = params["l1_size"]/params["dwell_time"]*S*T
                    if scan_vel > mvel:
                        print("scan velocity too high")
                        return False
                except:
                    p1egu = None
                    return False
                try:
                    p1llm = epics.caget(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "LLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "LLM:", p1llm)
                    if params["l1_center"]-params["l1_size"]/2 < p1llm:
                        print("l1_center - l1_size/2 < p1llm")
                        return False
                except:
                    p1llm = None
                    return False
                try:
                    p1hlm = epics.caget(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "HLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 1 PV")[:-3] + "HLM:", p1hlm)
                    if params["l1_center"]+params["l1_size"]/2 > p1hlm:
                        print("l1_center + l1_size/2 > p1hlm")
                        return False
                except:
                    p1hlm = None
                    return False
            else:
                mvel = None
                p1llm = None
                p1hlm = None
                print(" Positioner 1 not a standard motor")
            
        if self.settings_dialog.get_setting("Positioner 2 PV") != "":
            if self.settings_dialog.get_setting("Positioner 2 PV").split(":")[1].split(".")[0][0]=="m":
                try:
                    p2egu = epics.caget(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "EGU", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "EGU:", p2egu)
                except:
                    p2egu = None
                    return False
                try:
                    p2llm = epics.caget(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "LLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "LLM:", p2llm)
                except:
                    p2llm = None
                    return False
                try:
                    p2hlm = epics.caget(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "HLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "HLM:", p2hlm)
                    if params["l2_center"]+params["l2_size"]/2 > p2hlm:
                        print("l2_center + l2_size/2 > p2hlm")
                        return False
                except:
                    p2hlm = None
                    return False
            else:
                p2llm = None
                p2hlm = None
                print(" Positioner 2 not a standard motor")


        if self.settings_dialog.get_setting("Positioner 2 PV") != "":
            if self.settings_dialog.get_setting("Positioner 2 PV").split(":")[1].split(".")[0][0]=="m":
                try:
                    p2egu = epics.caget(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "EGU", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "EGU:", p2egu)
                except:
                    p2egu = None
                    print(" cannot connect to Positioner 2 EGU")
                try:
                    p2llm = epics.caget(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "LLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "LLM:", p2llm)
                    if params["l2_center"]-params["l2_size"]/2 < p2llm:
                        print("l2_center - l2_size/2 < p2llm")
                        return False
                except:
                    p2llm = None
                    print(" cannot connect to Positioner 2 LLM")
                try:
                    p2hlm = epics.caget(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "HLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 2 PV")[:-3] + "HLM:", p2hlm)
                except:
                    p2hlm = None
                    print(" cannot connect to Positioner 2 HLM")
            else:
                p3llm = None
                p3hlm = None
                print(" Positioner 3 not a standard motor")


        if self.settings_dialog.get_setting("Positioner 3 PV") != "":
            if self.settings_dialog.get_setting("Positioner 3 PV").split(":")[1].split(".")[0][0]=="m":
                try:
                    p3egu = epics.caget(self.settings_dialog.get_setting("Positioner 3 PV")[:-3] + "EGU", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 3 PV")[:-3] + "EGU:", p3egu)
                except:
                    p3egu = None
                    return False
                try:
                    p3llm = epics.caget(self.settings_dialog.get_setting("Positioner 3 PV")[:-3] + "LLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 3 PV")[:-3] + "LLM:", p3llm)
                    if params["l3_center"]-params["l3_size"]/2 < p3llm:
                        print("l3_center - l3_size/2 < p3llm")
                        return False
                except:
                    p3llm = None
                    return False
                try:
                    p3hlm = epics.caget(self.settings_dialog.get_setting("Positioner 3 PV")[:-3] + "HLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 3 PV")[:-3] + "HLM:", p3hlm)
                    if params["l3_center"]+params["l3_size"]/2 > p3hlm:
                        print("l3_center + l3_size/2 > p3hlm")
                        return False
                except:
                    p3hlm = None
                    return False
            else:
                p3llm = None
                p3hlm = None
                print(" Positioner 3 not a standard motor")

        if self.settings_dialog.get_setting("Positioner 4 PV") != "":
            if self.settings_dialog.get_setting("Positioner 4 PV").split(":")[1].split(".")[0][0]=="m":
                try:
                    p4llm = epics.caget(self.settings_dialog.get_setting("Positioner 4 PV")[:-3] + "LLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 4 PV")[:-3] + "LLM:", p4llm)
                    if params["l4_center"]-params["l4_size"]/2 < p4llm:
                        print("l4_center - l4_size/2 < p4llm")
                        return False
                except:
                    p4llm = None
                    return False
                try:
                    p4hlm = epics.caget(self.settings_dialog.get_setting("Positioner 4 PV")[:-3] + "HLM", connection_timeout=self.timeout)
                    print(self.settings_dialog.get_setting("Positioner 4 PV")[:-3] + "HLM:", p4hlm)
                    if params["l4_center"]+params["l4_size"]/2 > p4hlm:
                        print("l4_center + l4_size/2 > p4hlm")
                        return False
                except:
                    p4hlm = None
                    return False
            else:
                p4llm = None
                p4hlm = None
                print(" Positioner 4 not a standard motor")
        return True


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
        if line["line_action"].text() == "ready":
            try:
                params = self.get_params(line=line)
                params["pi_directory"] = self.controls.pi_dir.text()
                print("added to queue")
                self.send_to_queue(params)
            except: 
                print("could not add to queue")
                return
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
        self.id_counter += 1
        self.line_ids.append(self.id_counter)
        line_id = self.line_ids[-1]
        print("lineID", line_id)
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
        line.sendToQueueSig.connect(self.validate_params)

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
            try: 
                self.table_widget.removeRow(row_index)
            except Exception as e: 
                print(e)

    def queue_clear(self):
        try: 
            self.table_widget.setRowCount(0)
        except Exception as e: 
            print(e)
    
    def queue_item_move(self, idxs):
        try: 
            print(f"moving row from pos {idxs[0]} to pos {idxs[1]}")
            self.table_widget.moveRow(idxs[0], idxs[1])
        except Exception as e: 
            print(e)
        
    def queue_execute_now(self):
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
                params[key] = line[key].text()
            elif isinstance(line[key], ComboBoxWithPlaceholder):
                items = line[key].get_items()
                indices = line[key].checked_indices()
                try:
                    vals = [items[index-1] for index in indices]
                    if len(vals) == 0:
                        params[key] = ""
                    else:
                        params[key] = vals
                except:
                    params[key] = ""
            elif isinstance(line[key], QLabel):
                params[key] = line[key].text()
            elif isinstance(line[key], QLineEdit):
                if line[key].isVisible():
                    params[key] = line[key].text()
                else:
                    params[key] = ""
            else: 
                params[key] = line[key]
        return params

    def closeEvent(self, event):
        print("closing main window")
        self.save_lines_to_json()
        self.save_queue_to_json()
        self.save_pi_dir()
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

    def save_lines_to_json(self):
        """Save all Line objects to JSON file"""
        try:
            lines_data = []
            for i in range(self.lines_layout.count()):
                line_widget = self.lines_layout.itemAt(i).widget()
                if hasattr(line_widget, 'to_dict'):
                    lines_data.append(line_widget.to_dict())
            
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "lines_backup.json")
            
            with open(fname, 'w') as f:
                json.dump(lines_data, f, indent=2)
            print(f"Saved {len(lines_data)} lines to {fname}")
        except Exception as e:
            print(f"Error saving lines to JSON: {e}")

    def load_lines_from_json(self):
        """Load Line objects from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "lines_backup.json")
            
            if not os.path.exists(fname):
                print("No lines backup file found, starting with default lines")
                return
            
            with open(fname, 'r') as f:
                lines_data = json.load(f)
            
            if not lines_data:
                print("Empty lines backup file, starting with default lines")
                return
            
            # Clear existing lines
            while self.lines_layout.count():
                child = self.lines_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            self.line_ids = []
            self.id_counter = 0
            
            # Create new lines from saved data
            for line_data in lines_data:
                self.id_counter += 1
                line_id = self.id_counter
                self.line_ids.append(line_id)
                
                # Create new line with settings manager (no UI)
                setattr(self, f"line_{line_id}", Line(line_id, self.settings_manager))
                line = self.__dict__["line_{}".format(line_id)]
                
                # Connect signals
                line.setAutoFillBackground(True)
                line.addlinesig.connect(self.add_line)
                line.deletelinesig.connect(self.delete_line)
                line.duplicatelinesig.connect(self.duplicate_line)
                line.duplicatelinesig.connect(self.clear_line)
                line.sendToQueueSig.connect(self.enqueue_line)
                line.trajectoryChangedSig.connect(self.validate_params)
                line.lineditEnterdSig.connect(self.validate_params)
                line.sendToQueueSig.connect(self.validate_params)
                
                # Restore data
                line.from_dict(line_data)
                
                # Add to layout
                self.lines_layout.addWidget(line, alignment=QtCore.Qt.AlignLeft)
            
            print(f"Loaded {len(lines_data)} lines from {fname}")
        except Exception as e:
            print(f"Error loading lines from JSON: {e}")
            # If loading fails, create at least one default line
            if self.lines_layout.count() == 0:
                self.add_line()

    def save_queue_to_json(self):
        """Save queue table data to JSON file"""
        try:
            queue_data = {
                'headers': [],
                'rows': []
            }
            
            # Save headers
            for col in range(self.table_widget.columnCount()):
                header_item = self.table_widget.horizontalHeaderItem(col)
                if header_item:
                    queue_data['headers'].append(header_item.text())
                else:
                    queue_data['headers'].append(f"Column_{col}")
            
            # Save row data
            for row in range(self.table_widget.rowCount()):
                row_data = {}
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        row_data[queue_data['headers'][col]] = item.text()
                    else:
                        row_data[queue_data['headers'][col]] = ""
                queue_data['rows'].append(row_data)
            
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "queue_backup.json")
            
            with open(fname, 'w') as f:
                json.dump(queue_data, f, indent=2)
            print(f"Saved {len(queue_data['rows'])} queue items to {fname}")
        except Exception as e:
            print(f"Error saving queue to JSON: {e}")

    def load_queue_from_json(self):
        """Load queue table data from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "queue_backup.json")
            
            if not os.path.exists(fname):
                print("No queue backup file found, starting with empty queue")
                # Hide empty columns for empty queue as well
                self.table_widget.hide_empty_columns()
                return
            
            with open(fname, 'r') as f:
                queue_data = json.load(f)
            
            if not queue_data or 'rows' not in queue_data:
                print("Empty or invalid queue backup file, starting with empty queue")
                # Hide empty columns for empty queue as well
                self.table_widget.hide_empty_columns()
                return
            
            # Clear existing queue
            self.table_widget.setRowCount(0)
            
            # Restore headers if they match
            if 'headers' in queue_data:
                current_headers = [self.table_widget.horizontalHeaderItem(i).text() 
                                 for i in range(self.table_widget.columnCount())]
                if queue_data['headers'] != current_headers:
                    print("Warning: Queue headers don't match current configuration")
                    print(f"Saved headers: {queue_data['headers']}")
                    print(f"Current headers: {current_headers}")
            
            # Restore row data
            for row_data in queue_data['rows']:
                self.populate_next_available_row(self.table_widget, row_data)
            
            # Hide empty columns after loading data
            self.table_widget.hide_empty_columns()
            
            print(f"Loaded {len(queue_data['rows'])} queue items from {fname}")
        except Exception as e:
            print(f"Error loading queue from JSON: {e}")

    def save_pi_dir(self):
        """Save PI directory to JSON file"""
        try:
            pi_dir_data = {
                'pi_directory': self.controls.pi_dir.text()
            }
            
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "pi_dir_backup.json")
            
            with open(fname, 'w') as f:
                json.dump(pi_dir_data, f, indent=2)
            print(f"Saved PI directory to {fname}")
        except Exception as e:
            print(f"Error saving PI directory: {e}")

    def load_pi_dir(self):
        """Load PI directory from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
            fname = os.path.join(current_dir, "pi_dir_backup.json")
            
            if not os.path.exists(fname):
                print("No PI directory backup file found, using default")
                return
            
            with open(fname, 'r') as f:
                pi_dir_data = json.load(f)
            
            if 'pi_directory' in pi_dir_data:
                self.controls.pi_dir.setText(pi_dir_data['pi_directory'])
                print(f"Loaded PI directory: {pi_dir_data['pi_directory']}")
        except Exception as e:
            print(f"Error loading PI directory: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWindow = BatchScanGui(app)
    mainWindow.show()
    sys.exit(app.exec())
