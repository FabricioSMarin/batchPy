from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QComboBox, QCheckBox, QFrame, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder

class StatusLabel(QLabel):
    """Custom QLabel that emits a signal when text changes"""
    textChanged = pyqtSignal(str)
    
    def setText(self, text):
        """Override setText to emit signal when text changes"""
        if self.text() != text:
            super().setText(text)
            self.textChanged.emit(text)

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
        self.create_line_action_section(main_layout, size2, height)
        self.create_scan_type_section(main_layout, size1, height)
        self.create_detector_section(main_layout, size4, height)
        self.create_trajectory_section(main_layout, size2, height)
        self.create_loop_section(main_layout, size2, height)
        self.create_parameter_section(main_layout, size2, height)
        self.create_status_section(main_layout, size5, height)
        self.create_send_to_queue_button(main_layout, size2, height)
        
        self.setLayout(main_layout)
        
        # Add compatibility methods for trajectory and loops
        self._add_combo_compatibility_methods()
        
        # Initialize trajectory-based parameter visibility
        self.trajectory_changed()

    def create_line_action_section(self, parent_layout, size5, height):
        """Create line action section"""
        h_layout = QHBoxLayout()
        self.line_action_label = self._create_label("line action")
        h_layout.addWidget(self.line_action_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.line_action = QComboBox()
        self.line_action.setToolTip("line_action")
        # Add items to the combo box
        line_actions = ["normal", "skip", "pause"]
        self.line_action.addItems(line_actions)
        self.line_action.setCurrentText("normal")  # Set default to "normal"
        self.line_action.setFixedSize(size5, height)
        h_layout.addWidget(self.line_action)
        parent_layout.addLayout(h_layout)

    def create_scan_type_section(self, parent_layout, size1, height):
        """Create scan type section"""
        h_layout = QHBoxLayout()
        self.scan_type_label = self._create_label("scan type")
        h_layout.addWidget(self.scan_type_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.scan_type = QPushButton("step", checkable=True)
        self.scan_type.setToolTip("scan_type")
        self.scan_type.setFixedSize(size1, height)
        self.scan_type.clicked.connect(self.scan_type_changed)
        h_layout.addWidget(self.scan_type)
        parent_layout.addLayout(h_layout)

    def create_detector_section(self, parent_layout, size4, height):
        """Create detector section"""
        h_layout = QHBoxLayout()
        self.detectors_label = self._create_label("detectors")
        h_layout.addWidget(self.detectors_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.detectors = ComboBoxWithPlaceholder("detectors")
        self.detectors.setToolTip("detectors")
        detectors = ["xspress3", "tetramm", "xmap", "eiger", "interferometers"]
        self.detectors.addItems(detectors)
        self.detectors.setFixedSize(size4, height)
        self.detectors.check_selected([3])
        h_layout.addWidget(self.detectors)
        parent_layout.addLayout(h_layout)

    def create_trajectory_section(self, parent_layout, size5, height):
        """Create trajectory section"""
        h_layout = QHBoxLayout()
        self.trajectory_label = self._create_label("trajectory")
        h_layout.addWidget(self.trajectory_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.trajectory = QComboBox()
        self.trajectory.setToolTip("trajectory")
        trajectories = ["raster", "snake", "spiral", "lissajous", "custom"]
        self.trajectory.addItems(trajectories)
        self.trajectory.setFixedSize(size5, height)
        self.trajectory.setCurrentIndex(1)
        self.trajectory.currentIndexChanged.connect(self.trajectory_changed)
        h_layout.addWidget(self.trajectory)
        parent_layout.addLayout(h_layout)

    def create_loop_section(self, parent_layout, size5, height):
        """Create loop section"""
        # Get positioner options from settings
        positioner_options = self.get_positioner_options()
        
        self.loop1 = QComboBox()
        self.loop1.setToolTip("loop1")
        self.loop2 = QComboBox()
        self.loop2.setToolTip("loop2")
        self.loop3 = QComboBox()
        self.loop3.setToolTip("loop3")
        self.loop4 = QComboBox()
        self.loop4.setToolTip("loop4")
        
        # Add empty string as first item (to indicate loop not used), then positioner options
        for loop in [self.loop1, self.loop2, self.loop3, self.loop4]:
            loop.addItem("")  # Empty string to indicate loop not used
            loop.addItems(positioner_options)
            loop.setFixedSize(size5, height)
            loop.currentIndexChanged.connect(self.loop_changed)
        
        # Set default selections (index 0 is empty string, so add 1 to positioner indices)
        try:
            if len(positioner_options) > 0:
                self.loop1.setCurrentIndex(1)  # First positioner (index 1, since 0 is empty)
            if len(positioner_options) > 1:
                self.loop2.setCurrentIndex(2)  # Second positioner (index 2, since 0 is empty)
        except (IndexError, ValueError):
            self.loop1.setCurrentIndex(0)  # Set to empty string
            self.loop2.setCurrentIndex(0)  # Set to empty string
        
        h_layout1 = QHBoxLayout()
        self.loop1_label = self._create_label("loop 1")
        h_layout1.addWidget(self.loop1_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        h_layout1.addWidget(self.loop1)
        parent_layout.addLayout(h_layout1)
        
        h_layout2 = QHBoxLayout()
        self.loop2_label = self._create_label("loop 2")
        h_layout2.addWidget(self.loop2_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        h_layout2.addWidget(self.loop2)
        parent_layout.addLayout(h_layout2)
        
        h_layout3 = QHBoxLayout()
        self.loop3_label = self._create_label("loop 3")
        h_layout3.addWidget(self.loop3_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        h_layout3.addWidget(self.loop3)
        parent_layout.addLayout(h_layout3)
        
        h_layout4 = QHBoxLayout()
        self.loop4_label = self._create_label("loop 4")
        h_layout4.addWidget(self.loop4_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        h_layout4.addWidget(self.loop4)
        parent_layout.addLayout(h_layout4)

    def create_parameter_section(self, parent_layout, size2, height):
        """Create parameter section"""
        # Sample name
        h_layout = QHBoxLayout()
        self.sample_name_label = self._create_label("sample name")
        h_layout.addWidget(self.sample_name_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.sample_name = QLineEdit()
        self.sample_name.setToolTip("sample_name")
        self.sample_name.setPlaceholderText("sample name")
        self.sample_name.setFixedSize(size2, height)
        h_layout.addWidget(self.sample_name)
        parent_layout.addLayout(h_layout)
        
        # Dwell time
        h_layout = QHBoxLayout()
        self.dwell_time_label = self._create_label("dwell time (ms)")
        h_layout.addWidget(self.dwell_time_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.dwell_time = QLineEdit()
        self.dwell_time.setToolTip("dwell_time")
        self.dwell_time.setPlaceholderText("dwell time (ms)")
        self.dwell_time.setFixedSize(size2, height)
        h_layout.addWidget(self.dwell_time)
        parent_layout.addLayout(h_layout)
        
        # Loop 1 parameters
        h_layout = QHBoxLayout()
        self.l1_center_label = self._create_label("loop 1 center")
        h_layout.addWidget(self.l1_center_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l1_center = QLineEdit()
        self.l1_center.setToolTip("l1_center")
        self.l1_center.setPlaceholderText("center 1")
        self.l1_center.setFixedSize(size2, height)
        h_layout.addWidget(self.l1_center)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l1_size_label = self._create_label("loop 1 size")
        h_layout.addWidget(self.l1_size_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l1_size = QLineEdit()
        self.l1_size.setToolTip("l1_size")
        self.l1_size.setPlaceholderText("step size 1")
        self.l1_size.editingFinished.connect(self.update_width)
        self.l1_size.setFixedSize(size2, height)
        h_layout.addWidget(self.l1_size)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l1_width_label = self._create_label("loop 1 width")
        h_layout.addWidget(self.l1_width_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l1_width = QLineEdit()
        self.l1_width.setToolTip("l1_width")
        self.l1_width.setPlaceholderText("width 1")
        self.l1_width.setFixedSize(size2, height)
        h_layout.addWidget(self.l1_width)
        parent_layout.addLayout(h_layout)
        
        # Loop 2 parameters
        h_layout = QHBoxLayout()
        self.l2_center_label = self._create_label("loop 2 center")
        h_layout.addWidget(self.l2_center_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l2_center = QLineEdit()
        self.l2_center.setToolTip("l2_center")
        self.l2_center.setPlaceholderText("center 2")
        self.l2_center.setFixedSize(size2, height)
        h_layout.addWidget(self.l2_center)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l2_size_label = self._create_label("loop 2 size")
        h_layout.addWidget(self.l2_size_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l2_size = QLineEdit()
        self.l2_size.setToolTip("l2_size")
        self.l2_size.setPlaceholderText("step size 2")
        self.l2_size.setFixedSize(size2, height)
        self.l2_size.editingFinished.connect(self.update_width)
        h_layout.addWidget(self.l2_size)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l2_width_label = self._create_label("loop 2 width")
        h_layout.addWidget(self.l2_width_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l2_width = QLineEdit()
        self.l2_width.setToolTip("l2_width")
        self.l2_width.setPlaceholderText("width 2")
        self.l2_width.setFixedSize(size2, height)
        h_layout.addWidget(self.l2_width)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l3_center_label = self._create_label("loop 3 center")
        h_layout.addWidget(self.l3_center_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l3_center = QLineEdit()
        self.l3_center.setToolTip("l3_center")
        self.l3_center.setPlaceholderText("center 3")
        self.l3_center.setFixedSize(size2, height)
        h_layout.addWidget(self.l3_center)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l3_size_label = self._create_label("loop 3 size")
        h_layout.addWidget(self.l3_size_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l3_size = QLineEdit()
        self.l3_size.setToolTip("l3_size")
        self.l3_size.setPlaceholderText("step size 3")
        self.l3_size.setFixedSize(size2, height)
        h_layout.addWidget(self.l3_size)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l3_width_label = self._create_label("loop 3 width")
        h_layout.addWidget(self.l3_width_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l3_width = QLineEdit()
        self.l3_width.setToolTip("l3_width")
        self.l3_width.setPlaceholderText("width 3")
        self.l3_width.setFixedSize(size2, height)
        h_layout.addWidget(self.l3_width)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l4_center_label = self._create_label("loop 4 center")
        h_layout.addWidget(self.l4_center_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l4_center = QLineEdit()
        self.l4_center.setToolTip("l4_center")
        self.l4_center.setPlaceholderText("center 4")
        self.l4_center.setFixedSize(size2, height)
        h_layout.addWidget(self.l4_center)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l4_size_label = self._create_label("loop 4 size")
        h_layout.addWidget(self.l4_size_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l4_size = QLineEdit()
        self.l4_size.setToolTip("l4_size")
        self.l4_size.setPlaceholderText("step size 4")
        self.l4_size.setFixedSize(size2, height)
        h_layout.addWidget(self.l4_size)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.l4_width_label = self._create_label("loop 4 width")
        h_layout.addWidget(self.l4_width_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.l4_width = QLineEdit()
        self.l4_width.setToolTip("l4_width")
        self.l4_width.setPlaceholderText("width 4")
        self.l4_width.setFixedSize(size2, height)
        h_layout.addWidget(self.l4_width)
        parent_layout.addLayout(h_layout)
        
        # Additional trajectory-specific parameters
        h_layout = QHBoxLayout()
        self.tangential_step_label = self._create_label("tangential_step")
        h_layout.addWidget(self.tangential_step_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.tangential_step = QLineEdit()
        self.tangential_step.setToolTip("tangential_step")
        self.tangential_step.setPlaceholderText("tangential step")
        self.tangential_step.setFixedSize(size2, height)
        h_layout.addWidget(self.tangential_step)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.radial_step_label = self._create_label("radial_step")
        h_layout.addWidget(self.radial_step_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.radial_step = QLineEdit()
        self.radial_step.setToolTip("radial_step")
        self.radial_step.setPlaceholderText("radial step")
        self.radial_step.setFixedSize(size2, height)
        h_layout.addWidget(self.radial_step)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.diameter_label = self._create_label("diameter")
        h_layout.addWidget(self.diameter_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.diameter = QLineEdit()
        self.diameter.setToolTip("diameter")
        self.diameter.setPlaceholderText("diameter")
        self.diameter.setFixedSize(size2, height)
        h_layout.addWidget(self.diameter)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.cycles_label = self._create_label("cycles")
        h_layout.addWidget(self.cycles_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.cycles = QLineEdit()
        self.cycles.setToolTip("cycles")
        self.cycles.setPlaceholderText("cycles")
        self.cycles.setFixedSize(size2, height)
        h_layout.addWidget(self.cycles)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.x_freq_label = self._create_label("x_freq")
        h_layout.addWidget(self.x_freq_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.x_freq = QLineEdit()
        self.x_freq.setToolTip("x_freq")
        self.x_freq.setPlaceholderText("x frequency")
        self.x_freq.setFixedSize(size2, height)
        h_layout.addWidget(self.x_freq)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.y_freq_label = self._create_label("y_freq")
        h_layout.addWidget(self.y_freq_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.y_freq = QLineEdit()
        self.y_freq.setToolTip("y_freq")
        self.y_freq.setPlaceholderText("y frequency")
        self.y_freq.setFixedSize(size2, height)
        h_layout.addWidget(self.y_freq)
        parent_layout.addLayout(h_layout)
        
        # Comments field
        h_layout = QHBoxLayout()
        self.comments_label = self._create_label("comments")
        h_layout.addWidget(self.comments_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.comments = QLineEdit("")
        self.comments.setToolTip("comments")
        self.comments.setPlaceholderText("comments")
        self.comments.setFixedSize(size2, height)
        h_layout.addWidget(self.comments)
        parent_layout.addLayout(h_layout)
        
        # Connect all QLineEdit widgets to emit lineditEnterdSig when Enter is pressed
        self.connect_line_edits()

    def create_status_section(self, parent_layout, size5, height):
        """Create status section"""
        h_layout = QHBoxLayout()
        self.line_status_label = self._create_label("status")
        h_layout.addWidget(self.line_status_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.line_status = StatusLabel("not ready")
        self.line_status.setFixedSize(size5, height)
        self.line_status.setToolTip("line_status")
        # Connect textChanged signal to update button state
        self.line_status.textChanged.connect(self.update_send_to_queue_button_state)
        h_layout.addWidget(self.line_status)
        parent_layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.eta_label = self._create_label("eta (H:M:S)")
        h_layout.addWidget(self.eta_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.eta = QLabel("--:--:--")
        self.eta.setFixedSize(size5, height)
        self.eta.setToolTip("eta")
        h_layout.addWidget(self.eta)
        parent_layout.addLayout(h_layout)

    def create_send_to_queue_button(self, parent_layout, size2, height):
        """Create send to queue button at the bottom of the widget"""
        h_layout = QHBoxLayout()
        self.send_to_queue_button = QPushButton("send to queue")
        self.send_to_queue_button.setToolTip("send to queue")
        self.send_to_queue_button.setFixedSize(size2, height)
        self.send_to_queue_button.clicked.connect(lambda: self.sendToQueueSig.emit(self.id))
        self.send_to_queue_button.setEnabled(False)  # Initially disabled
        h_layout.addWidget(self.send_to_queue_button, alignment=Qt.AlignCenter)
        parent_layout.addLayout(h_layout)
        
        # Update button state based on initial status
        self.update_send_to_queue_button_state()

    def update_send_to_queue_button_state(self):
        """Update the send to queue button enabled state based on status"""
        if hasattr(self, 'send_to_queue_button') and hasattr(self, 'line_status'):
            is_ready = self.line_status.text().lower() == "ready"
            self.send_to_queue_button.setEnabled(is_ready)
    
    def set_status(self, status_text):
        """Set the status text and update the send to queue button state"""
        if hasattr(self, 'line_status'):
            self.line_status.setText(status_text)
            self.update_send_to_queue_button_state()

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
            current_trajectory = self.trajectory.currentText()
            print(f"Trajectory changed to: {current_trajectory}")
            
            # Hide all parameters by default
            self._set_visibility([
                "dwell_time", "l1_center", "l1_size", "l1_width",
                "l2_center", "l2_size", "l2_width", "l3_center", "l3_size", "l3_width",
                "l4_center", "l4_size", "l4_width", "tangential_step", "radial_step",
                "diameter", "x_freq", "y_freq", "cycles"
            ], False)

            self.loop_changed()

            # Show relevant parameters
            if current_trajectory == "raster" or current_trajectory == "snake":
                self._set_visibility([
                    "dwell_time", "l1_center", "l1_size", "l1_width",
                    "l2_center", "l2_size", "l2_width"
                ], True)

            elif current_trajectory == "spiral":
                self._set_visibility([
                    "dwell_time", "tangential_step", "radial_step", "diameter"
                ], True)

            elif current_trajectory == "lissajous":
                self._set_visibility([
                    "dwell_time", "tangential_step", "x_freq", "y_freq", "cycles"
                ], True)

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
            # Check if loops are selected (index 0 is empty string, so loop is not used)
            loop1_selected = self.loop1.currentIndex() > 0 and self.loop1.currentText() != ""
            loop2_selected = self.loop2.currentIndex() > 0 and self.loop2.currentText() != ""
            loop3_selected = self.loop3.currentIndex() > 0 and self.loop3.currentText() != ""
            loop4_selected = self.loop4.currentIndex() > 0 and self.loop4.currentText() != ""

            # Show/hide loop 1 parameters
            if loop1_selected:
                self._set_visibility(["l1_center", "l1_size", "l1_width"], False)
            else: 
                self._set_visibility(["l1_center", "l1_size", "l1_width"], True)

            # Show/hide loop 2 parameters
            if not loop2_selected:
                self._set_visibility(["l2_center", "l2_size", "l2_width"], False)
            else: 
                self._set_visibility(["l2_center", "l2_size", "l2_width"], True)
                
            if not loop3_selected:
                self._set_visibility(["l3_center", "l3_size", "l3_width"], False)
            else: 
                self._set_visibility(["l3_center", "l3_size", "l3_width"], True)

            if not loop4_selected:
                self._set_visibility(["l4_center", "l4_size", "l4_width"], False)
            else: 
                self._set_visibility(["l4_center", "l4_size", "l4_width"], True)
        except Exception as e:
            print(f"Error in loop_changed: {e}")
            pass

    def update_width(self):
        """Update width calculation"""
        # Implement width update logic
        # Also emit the signal when editing is finished
        self.lineditEnterdSig.emit()

    def on_line_edit_entered(self):
        """Handle when Enter is pressed in any QLineEdit"""
        self.lineditEnterdSig.emit()

    def connect_line_edits(self):
        """Connect all QLineEdit widgets to emit lineditEnterdSig when Enter is pressed"""
        line_edit_widgets = [
            self.sample_name, self.dwell_time, self.l1_center, self.l1_size, self.l1_width,
            self.l2_center, self.l2_size, self.l2_width, self.l3_center, self.l3_size, self.l3_width,
            self.l4_center, self.l4_size, self.l4_width, self.tangential_step, self.radial_step,
            self.diameter, self.cycles, self.x_freq, self.y_freq, self.comments
        ]
        
        for widget in line_edit_widgets:
            if widget:  # Make sure the widget exists
                widget.returnPressed.connect(self.on_line_edit_entered)

    def _set_visibility(self, names, visible):
        """Set visibility for widgets and their corresponding labels."""
        for name in names:
            widget = getattr(self, name, None)
            if widget:
                widget.setVisible(visible)
            label = getattr(self, f"{name}_label", None)
            if label:
                label.setVisible(visible)

    def _create_label(self, text):
        """Create a label with consistent width."""
        label = QLabel(text)
        label.setFixedWidth(85)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        label.setStyleSheet("background: transparent; border: none;")
        return label
    
    def _get_combo_checked_names(self, combo):
        """Get checked names from QComboBox (returns list for compatibility)."""
        idx = combo.currentIndex()
        # Index 0 is empty string (not used), so return empty list
        if idx > 0:
            return [combo.currentText()]
        return []
    
    def _get_combo_checked_indices(self, combo):
        """Get checked indices from QComboBox (returns list for compatibility)."""
        idx = combo.currentIndex()
        # Index 0 is empty string (not used), so return empty list
        if idx > 0:
            return [idx]
        return []
    
    def _set_combo_selected(self, combo, indices):
        """Set selected index in QComboBox from list of indices."""
        if indices and len(indices) > 0 and indices[0] > 0:
            combo.setCurrentIndex(indices[0])
        else:
            # Set to index 0 (empty string) to indicate not used
            combo.setCurrentIndex(0)
    
    # Compatibility methods for trajectory and loops to maintain API
    def _add_combo_compatibility_methods(self):
        """Add compatibility methods to QComboBox widgets to match ComboBoxWithPlaceholder API."""
        # Add methods to line_action
        self.line_action.check_selected = lambda indices: self._set_combo_selected(self.line_action, indices)
        self.line_action.checked_names = lambda: self._get_combo_checked_names(self.line_action)
        self.line_action.checked_indices = lambda: self._get_combo_checked_indices(self.line_action)
        
        # Add methods to trajectory
        self.trajectory.check_selected = lambda indices: self._set_combo_selected(self.trajectory, indices)
        self.trajectory.checked_names = lambda: self._get_combo_checked_names(self.trajectory)
        self.trajectory.checked_indices = lambda: self._get_combo_checked_indices(self.trajectory)
        
        # Add methods to loops
        for loop_name in ['loop1', 'loop2', 'loop3', 'loop4']:
            loop_widget = getattr(self, loop_name)
            loop_widget.check_selected = lambda indices, widget=loop_widget: self._set_combo_selected(widget, indices)
            loop_widget.checked_names = lambda widget=loop_widget: self._get_combo_checked_names(widget)
            loop_widget.checked_indices = lambda widget=loop_widget: self._get_combo_checked_indices(widget)

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
                # Skip styling for newly created labels (those ending with _label)
                if not key.endswith("_label"):
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
            'line_action': {
                'checked_names': self._get_combo_checked_names(self.line_action),
                'checked_indices': self._get_combo_checked_indices(self.line_action)
            },
            'detectors': {
                'checked_names': self.detectors.checked_names(),
                'checked_indices': self.detectors.checked_indices()
            },
            'trajectory': {
                'checked_names': self._get_combo_checked_names(self.trajectory),
                'checked_indices': self._get_combo_checked_indices(self.trajectory)
            },
            'loop1': {
                'checked_names': self._get_combo_checked_names(self.loop1),
                'checked_indices': self._get_combo_checked_indices(self.loop1)
            },
            'loop2': {
                'checked_names': self._get_combo_checked_names(self.loop2),
                'checked_indices': self._get_combo_checked_indices(self.loop2)
            },
            'loop3': {
                'checked_names': self._get_combo_checked_names(self.loop3),
                'checked_indices': self._get_combo_checked_indices(self.loop3)
            },
            'loop4': {
                'checked_names': self._get_combo_checked_names(self.loop4),
                'checked_indices': self._get_combo_checked_indices(self.loop4)
            },
            'line_status': self.line_status.text(),
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
        
        # Restore line_action (QComboBox) - handle both old and new formats
        if 'line_action' in data:
            line_action_data = data['line_action']
            # New format: dictionary with checked_indices
            if isinstance(line_action_data, dict) and 'checked_indices' in line_action_data:
                self._set_combo_selected(self.line_action, line_action_data['checked_indices'])
            # Old format: string (this was the status, ignore it as we now have line_status)
            # Just skip it - the old line_action string will be handled by line_status restoration below
        
        # Restore detectors
        if 'detectors' in data:
            self.detectors.check_selected(data['detectors']['checked_indices'])
        
        # Restore trajectory
        if 'trajectory' in data:
            trajectory_data = data['trajectory']
            if isinstance(trajectory_data, dict) and 'checked_indices' in trajectory_data:
                self._set_combo_selected(self.trajectory, trajectory_data['checked_indices'])
        
        # Restore loops
        for loop_name in ['loop1', 'loop2', 'loop3', 'loop4']:
            if loop_name in data:
                loop_data = data[loop_name]
                if isinstance(loop_data, dict) and 'checked_indices' in loop_data:
                    loop_widget = getattr(self, loop_name)
                    self._set_combo_selected(loop_widget, loop_data['checked_indices'])
        
        # Restore text fields
        text_fields = [
            'line_status', 'eta', 'sample_name', 'dwell_time', 'l1_center', 'l1_size', 'l1_width',
            'l2_center', 'l2_size', 'l2_width', 'l3_center', 'l3_size', 'l3_width', 'l4_center', 'l4_size', 'l4_width', 
            'tangential_step', 'radial_step', 'diameter', 'cycles', 'x_freq', 'y_freq', 'comments'
        ]
        
        for field in text_fields:
            if field in data:
                widget = getattr(self, field)
                if hasattr(widget, 'setText'):
                    widget.setText(data[field])
        
        # Backward compatibility: if old format has 'line_action' as string (status), map it to line_status
        if 'line_action' in data and isinstance(data['line_action'], str) and 'line_status' not in data:
            if hasattr(self, 'line_status'):
                self.line_status.setText(data['line_action'])
        
        # Trigger UI updates
        self.trajectory_changed()
        self.update_send_to_queue_button_state()
