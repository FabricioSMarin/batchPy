from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QComboBox, QCheckBox, QFrame
from PyQt5.QtCore import pyqtSignal
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder

class VerticalLine(QWidget):
    sendToQueueSig = pyqtSignal(int)
    trajectoryChangedSig = pyqtSignal()
    lineditEnterdSig = pyqtSignal()
    paramsChangedSig = pyqtSignal(int)
    addlinesig = pyqtSignal()
    deletelinesig = pyqtSignal(int)
    duplicatelinesig = pyqtSignal(int)
    clearlinesig = pyqtSignal(int)

    def __init__(self, line_id, settings_dialog=None):
        super(VerticalLine, self).__init__()
        self.id = line_id
        self.settings_dialog = settings_dialog
        self.setupUi()
        self.make_pretty()

    def contextMenuEvent(self, pos):
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
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        self.setStyleSheet("background: white")
        
        # Create sections with horizontal layouts for better organization
        self.create_scan_type_section(main_layout, size1, height)
        self.create_detector_section(main_layout, size4, height)
        self.create_trajectory_section(main_layout, size5, height)
        self.create_loop_section(main_layout, size5, height)
        self.create_parameter_section(main_layout, size2, height)
        self.create_status_section(main_layout, size5, height)
        
        self.setLayout(main_layout)
        
        # Initialize trajectory-based parameter visibility
        self.trajectory_changed()

    def create_scan_type_section(self, parent_layout, size1, height):
        """Create scan type section"""
        self.scan_type = QPushButton("step", checkable=True)
        self.scan_type.setToolTip("scan_type")
        self.scan_type.setFixedSize(size1, height)
        self.scan_type.clicked.connect(self.scan_type_changed)
        parent_layout.addWidget(self.scan_type)

    def create_detector_section(self, parent_layout, size4, height):
        """Create detector section"""
        self.detectors = ComboBoxWithPlaceholder("detectors")
        self.detectors.setToolTip("detectors")
        detectors = ["xspress3", "tetramm", "xmap", "eiger", "interferometers"]
        self.detectors.addItems(detectors)
        self.detectors.setFixedSize(size4, height)
        self.detectors.check_selected([3])
        parent_layout.addWidget(self.detectors)

    def create_trajectory_section(self, parent_layout, size5, height):
        """Create trajectory section"""
        self.trajectory = ComboBoxWithPlaceholder("trajectory", exclusive=True)
        self.trajectory.setToolTip("trajectory")
        trajectories = ["raster", "snake", "spiral", "lissajous", "custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedSize(size5, height)
        self.trajectory.check_selected([1])
        self.trajectory.model().itemChanged.connect(self.trajectory_changed)
        parent_layout.addWidget(self.trajectory)

    def create_loop_section(self, parent_layout, size5, height):
        """Create loop section"""
        # Get positioner options from settings
        positioner_options = self.get_positioner_options()
        
        self.loop1 = ComboBoxWithPlaceholder("loop1", exclusive=True)
        self.loop1.setToolTip("loop1")
        self.loop2 = ComboBoxWithPlaceholder("loop2", exclusive=True)
        self.loop2.setToolTip("loop2")
        self.loop3 = ComboBoxWithPlaceholder("loop3", exclusive=True)
        self.loop3.setToolTip("loop3")
        self.loop4 = ComboBoxWithPlaceholder("loop4", exclusive=True)
        self.loop4.setToolTip("loop4")
        
        # Add positioner options to all loops
        for loop in [self.loop1, self.loop2, self.loop3, self.loop4]:
            loop.addItems(positioner_options)
            loop.setFixedSize(size5, height)
            loop.model().itemChanged.connect(self.loop_changed)
        
        # Set default selections
        try:
            if len(positioner_options) > 0:
                self.loop1.check_selected([1])
            if len(positioner_options) > 1:
                self.loop2.check_selected([2])
        except (IndexError, ValueError):
            self.loop1.check_selected([])
            self.loop2.check_selected([])
        
        parent_layout.addWidget(self.loop1)
        parent_layout.addWidget(self.loop2)
        parent_layout.addWidget(self.loop3)
        parent_layout.addWidget(self.loop4)

    def create_parameter_section(self, parent_layout, size2, height):
        """Create parameter section"""
        # Sample name
        self.sample_name = QLineEdit()
        self.sample_name.setToolTip("sample_name")
        self.sample_name.setPlaceholderText("sample name")
        self.sample_name.setFixedSize(size2, height)
        parent_layout.addWidget(self.sample_name)
        
        # Dwell time
        self.dwell_time = QLineEdit()
        self.dwell_time.setToolTip("dwell_time")
        self.dwell_time.setPlaceholderText("dwell time (ms)")
        self.dwell_time.setFixedSize(size2, height)
        parent_layout.addWidget(self.dwell_time)
        
        # Loop 1 parameters
        self.l1_center = QLineEdit()
        self.l1_center.setToolTip("l1_center")
        self.l1_center.setPlaceholderText("center 1")
        self.l1_center.setFixedSize(size2, height)
        parent_layout.addWidget(self.l1_center)
        
        self.l1_size = QLineEdit()
        self.l1_size.setToolTip("l1_size")
        self.l1_size.setPlaceholderText("step size 1")
        self.l1_size.editingFinished.connect(self.update_width)
        self.l1_size.setFixedSize(size2, height)
        parent_layout.addWidget(self.l1_size)
        
        self.l1_width = QLineEdit()
        self.l1_width.setToolTip("l1_width")
        self.l1_width.setPlaceholderText("width 1")
        self.l1_width.setFixedSize(size2, height)
        parent_layout.addWidget(self.l1_width)
        
        # Loop 2 parameters
        self.l2_center = QLineEdit()
        self.l2_center.setToolTip("l2_center")
        self.l2_center.setPlaceholderText("center 2")
        self.l2_center.setFixedSize(size2, height)
        parent_layout.addWidget(self.l2_center)
        
        self.l2_size = QLineEdit()
        self.l2_size.setToolTip("l2_size")
        self.l2_size.setPlaceholderText("step size 2")
        self.l2_size.setFixedSize(size2, height)
        self.l2_size.editingFinished.connect(self.update_width)
        parent_layout.addWidget(self.l2_size)
        
        self.l2_width = QLineEdit()
        self.l2_width.setToolTip("l2_width")
        self.l2_width.setPlaceholderText("width 2")
        self.l2_width.setFixedSize(size2, height)
        parent_layout.addWidget(self.l2_width)
        
        self.l3_center = QLineEdit()
        self.l3_center.setToolTip("l3_center")
        self.l3_center.setPlaceholderText("center 3")
        self.l3_center.setFixedSize(size2, height)
        parent_layout.addWidget(self.l3_center)
        
        self.l3_size = QLineEdit()
        self.l3_size.setToolTip("l3_size")
        self.l3_size.setPlaceholderText("step size 3")
        self.l3_size.setFixedSize(size2, height)
        parent_layout.addWidget(self.l3_size)
        
        self.l3_width = QLineEdit()
        self.l3_width.setToolTip("l3_width")
        self.l3_width.setPlaceholderText("width 3")
        self.l3_width.setFixedSize(size2, height)
        parent_layout.addWidget(self.l3_width)
        
        self.l4_center = QLineEdit()
        self.l4_center.setToolTip("l4_center")
        self.l4_center.setPlaceholderText("center 4")
        self.l4_center.setFixedSize(size2, height)
        parent_layout.addWidget(self.l4_center)
        
        self.l4_size = QLineEdit()
        self.l4_size.setToolTip("l4_size")
        self.l4_size.setPlaceholderText("step size 4")
        self.l4_size.setFixedSize(size2, height)
        parent_layout.addWidget(self.l4_size)
        
        self.l4_width = QLineEdit()
        self.l4_width.setToolTip("l4_width")
        self.l4_width.setPlaceholderText("width 4")
        self.l4_width.setFixedSize(size2, height)
        parent_layout.addWidget(self.l4_width)
        
        # Additional trajectory-specific parameters
        self.tangential_step = QLineEdit()
        self.tangential_step.setToolTip("tangential_step")
        self.tangential_step.setPlaceholderText("tangential step")
        self.tangential_step.setFixedSize(size2, height)
        parent_layout.addWidget(self.tangential_step)
        
        self.radial_step = QLineEdit()
        self.radial_step.setToolTip("radial_step")
        self.radial_step.setPlaceholderText("radial step")
        self.radial_step.setFixedSize(size2, height)
        parent_layout.addWidget(self.radial_step)
        
        self.diameter = QLineEdit()
        self.diameter.setToolTip("diameter")
        self.diameter.setPlaceholderText("diameter")
        self.diameter.setFixedSize(size2, height)
        parent_layout.addWidget(self.diameter)
        
        self.cycles = QLineEdit()
        self.cycles.setToolTip("cycles")
        self.cycles.setPlaceholderText("cycles")
        self.cycles.setFixedSize(size2, height)
        parent_layout.addWidget(self.cycles)
        
        self.x_freq = QLineEdit()
        self.x_freq.setToolTip("x_freq")
        self.x_freq.setPlaceholderText("x frequency")
        self.x_freq.setFixedSize(size2, height)
        parent_layout.addWidget(self.x_freq)
        
        self.y_freq = QLineEdit()
        self.y_freq.setToolTip("y_freq")
        self.y_freq.setPlaceholderText("y frequency")
        self.y_freq.setFixedSize(size2, height)
        parent_layout.addWidget(self.y_freq)
        
        # Comments field
        self.comments = QLineEdit("")
        self.comments.setToolTip("comments")
        self.comments.setPlaceholderText("comments")
        self.comments.setFixedSize(size2, height)
        parent_layout.addWidget(self.comments)

    def create_status_section(self, parent_layout, size5, height):
        """Create status section"""
        self.line_action = QLabel("not ready")
        self.line_action.setFixedSize(size5, height)
        self.line_action.setToolTip("line_action")
        parent_layout.addWidget(self.line_action)
        
        self.eta = QLabel("--:--:--")
        self.eta.setFixedSize(size5, height)
        self.eta.setToolTip("eta")
        parent_layout.addWidget(self.eta)

    def get_positioner_options(self):
        """Get positioner options from settings"""
        try:
            if self.settings_dialog and hasattr(self.settings_dialog, 'get_setting'):
                positioners = []
                for i in range(1, 5):  # Positioner 1-4
                    pv_key = f"Positioner {i} PV"
                    pv_value = self.settings_dialog.get_setting(pv_key)
                    
                    if pv_value and pv_value.strip():
                        positioners.append(pv_value)  # Use the actual PV value, not the label
                
                # Add some default options if no positioners are configured
                if not positioners:
                    positioners = ["Positioner 1 PV", "Positioner 2 PV", "Positioner 3 PV", "Positioner 4 PV"]
                
                return positioners
            else:
                # Fallback to default options if no settings available
                return ["Positioner 1 PV", "Positioner 2 PV", "Positioner 3 PV", "Positioner 4 PV"]
        except Exception as e:
            print(f"Error getting positioner options: {e}")
            return ["Positioner 1 PV", "Positioner 2 PV", "Positioner 3 PV", "Positioner 4 PV"]

    def scan_type_changed(self):
        """Handle scan type change"""
        if self.scan_type.isChecked():
            self.scan_type.setText("fly")
        else:
            self.scan_type.setText("step")

    def trajectory_changed(self):
        """Handle trajectory change - show/hide parameters based on trajectory type"""
        try:
            current_trajectory = self.trajectory.checked_names()[0]
            print(f"Trajectory changed to: {current_trajectory}")
            
            # Hide all parameters by default
            self.dwell_time.setVisible(False)
            self.l1_center.setVisible(False)
            self.l1_size.setVisible(False)
            self.l1_width.setVisible(False)
            self.l2_center.setVisible(False)
            self.l2_size.setVisible(False)
            self.l2_width.setVisible(False)
            self.l3_center.setVisible(False)
            self.l3_size.setVisible(False)
            self.l3_width.setVisible(False)
            self.l4_center.setVisible(False)
            self.l4_size.setVisible(False)
            self.l4_width.setVisible(False)
            self.tangential_step.setVisible(False)
            self.radial_step.setVisible(False)
            self.diameter.setVisible(False)
            self.x_freq.setVisible(False)
            self.y_freq.setVisible(False)
            self.cycles.setVisible(False)

            self.loop_changed()

            # Show relevant parameters
            if current_trajectory == "raster" or current_trajectory == "snake":
                self.dwell_time.setVisible(True)
                self.l1_center.setVisible(True)
                self.l1_size.setVisible(True)
                self.l1_width.setVisible(True)
                self.l2_center.setVisible(True)
                self.l2_size.setVisible(True)
                self.l2_width.setVisible(True)

            elif current_trajectory == "spiral":
                self.dwell_time.setVisible(True)
                self.tangential_step.setVisible(True)
                self.radial_step.setVisible(True)
                self.diameter.setVisible(True)

            elif current_trajectory == "lissajous":
                self.dwell_time.setVisible(True)
                self.tangential_step.setVisible(True)
                self.x_freq.setVisible(True)
                self.y_freq.setVisible(True)
                self.cycles.setVisible(True)

            elif current_trajectory == "custom":
                pass

            # Apply styling to all QLineEdit widgets
            for key in self.__dict__:
                item = getattr(self, key)
                if isinstance(item, QLineEdit):
                    if item.isEnabled():
                        item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
                    else:
                        item.setStyleSheet("background: lightblue; color: lightblue; border-radius: 4")
                        
        except Exception as e:
            print(f"Error in trajectory_changed: {e}")
            pass
        
        self.trajectoryChangedSig.emit()

    def loop_changed(self):
        """Handle loop change - show/hide parameter fields based on selected loops"""
        try:
            loop1 = self.loop1.checked_names()
            loop2 = self.loop2.checked_names()
            loop3 = self.loop3.checked_names()
            loop4 = self.loop4.checked_names()

            # Show/hide loop 1 parameters
            if len(loop1) != 0:
                self.l1_center.setVisible(False)
                self.l1_size.setVisible(False)
                self.l1_width.setVisible(False)
            else: 
                self.l1_center.setVisible(True)
                self.l1_size.setVisible(True)
                self.l1_width.setVisible(True)

            # Show/hide loop 2 parameters
            if len(loop2) == 0:
                self.l2_center.setVisible(False)
                self.l2_size.setVisible(False)
                self.l2_width.setVisible(False)
            else: 
                self.l2_center.setVisible(True)
                self.l2_size.setVisible(True)
                self.l2_width.setVisible(True)
                
            if len(loop3) == 0:
                self.l3_center.setVisible(False)
                self.l3_size.setVisible(False)
                self.l3_width.setVisible(False)
            else: 
                self.l3_center.setVisible(True)
                self.l3_size.setVisible(True)
                self.l3_width.setVisible(True)

            if len(loop4) == 0:
                self.l4_center.setVisible(False)
                self.l4_size.setVisible(False)
                self.l4_width.setVisible(False)
            else: 
                self.l4_center.setVisible(True)
                self.l4_size.setVisible(True)
                self.l4_width.setVisible(True)
        except Exception as e:
            print(f"Error in loop_changed: {e}")
            pass

    def update_width(self):
        """Update width calculation"""
        # Implement width update logic
        pass

    def make_pretty(self):
        """Apply styling to the widget - matches original Line widget styling"""
        myFont = QtGui.QFont()
        myFont.setBold(True)
        myFont.setPointSize(9)

        for key in self.__dict__:
            item = getattr(self, key)
            if isinstance(item, QLineEdit):
                item.setStyleSheet("background: lightblue; color: black; border-radius: 4")
            elif isinstance(item, QCheckBox):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item, QLabel):
                item.setStyleSheet("background: lightgray;color: black; border-radius: 4; border-color: white")
            elif isinstance(item, QComboBox):
                item.setStyleSheet("background: lightyellow; color: black")
            elif isinstance(item, QPushButton):
                item.setStyleSheet("QPushButton {background: lightgreen;color: black; border-radius: 4;}" "QPushButton::checked {background-color: orchid;}")
            else:
                pass
        return

    def to_dict(self):
        """Convert VerticalLine object to a dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'scan_type': {
                'text': self.scan_type.text(),
                'checked': self.scan_type.isChecked()
            },
            'detectors': {
                'checked_names': self.detectors.checked_names(),
                'checked_indices': self.detectors.checked_indices()
            },
            'trajectory': {
                'checked_names': self.trajectory.checked_names(),
                'checked_indices': self.trajectory.checked_indices()
            },
            'loop1': {
                'checked_names': self.loop1.checked_names(),
                'checked_indices': self.loop1.checked_indices()
            },
            'loop2': {
                'checked_names': self.loop2.checked_names(),
                'checked_indices': self.loop2.checked_indices()
            },
            'loop3': {
                'checked_names': self.loop3.checked_names(),
                'checked_indices': self.loop3.checked_indices()
            },
            'loop4': {
                'checked_names': self.loop4.checked_names(),
                'checked_indices': self.loop4.checked_indices()
            },
            'line_action': self.line_action.text(),
            'eta': self.eta.text(),
            'sample_name': self.sample_name.text(),
            'dwell_time': self.dwell_time.text(),
            'l1_center': self.l1_center.text(),
            'l1_size': self.l1_size.text(),
            'l1_width': self.l1_width.text(),
            'l2_center': self.l2_center.text(),
            'l2_size': self.l2_size.text(),
            'l2_width': self.l2_width.text(),
            'l3_center': self.l3_center.text(),
            'l3_size': self.l3_size.text(),
            'l3_width': self.l3_width.text(),
            'l4_center': self.l4_center.text(),
            'l4_size': self.l4_size.text(),
            'l4_width': self.l4_width.text(),
            'tangential_step': self.tangential_step.text(),
            'radial_step': self.radial_step.text(),
            'diameter': self.diameter.text(),
            'cycles': self.cycles.text(),
            'x_freq': self.x_freq.text(),
            'y_freq': self.y_freq.text(),
            'comments': self.comments.text()
        }
        return data

    def from_dict(self, data):
        """Restore VerticalLine object from a dictionary"""
        if 'id' in data:
            self.id = data['id']
        
        # Restore scan_type
        if 'scan_type' in data:
            self.scan_type.setText(data['scan_type']['text'])
            self.scan_type.setChecked(data['scan_type']['checked'])
        
        # Restore detectors
        if 'detectors' in data:
            self.detectors.check_selected(data['detectors']['checked_indices'])
        
        # Restore trajectory
        if 'trajectory' in data:
            self.trajectory.check_selected(data['trajectory']['checked_indices'])
        
        # Restore loops
        for loop_name in ['loop1', 'loop2', 'loop3', 'loop4']:
            if loop_name in data:
                loop_widget = getattr(self, loop_name)
                loop_widget.check_selected(data[loop_name]['checked_indices'])
        
        # Restore text fields
        text_fields = [
            'line_action', 'eta', 'sample_name', 'dwell_time', 'l1_center', 'l1_size', 'l1_width',
            'l2_center', 'l2_size', 'l2_width', 'l3_center', 'l3_size', 'l3_width', 'l4_center', 'l4_size', 'l4_width', 
            'tangential_step', 'radial_step', 'diameter', 'cycles', 'x_freq', 'y_freq', 'comments'
        ]
        
        for field in text_fields:
            if field in data:
                widget = getattr(self, field)
                if hasattr(widget, 'setText'):
                    widget.setText(data[field])
        
        # Trigger UI updates
        self.trajectory_changed()
