
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QTextEdit, QCheckBox, QComboBox, QFileDialog
from ComboBoxWithPlaceholder import ComboBoxWithPlaceholder
from ImageView import ImageView

class Controls(QWidget):
    def __init__(self, settings_manager=None):
        super(Controls, self).__init__()
        self.settings_manager = settings_manager
        self.setupUi()

    def setupUi(self):
        size1 = 30
        size2 = 60
        size3 = 110
        size4 = 200
        size5 = 500
        height = 25
        eta_lbl = QLabel("ETA")
        eta_lbl.setFixedSize(size1,height)
        self.eta = QLabel("0")
        self.eta.setFixedSize(size4,height)

        pi_dir_lbl = QLabel("PI directory")
        pi_dir_lbl.setFixedSize(size1,height)
        self.pi_dir= QLineEdit("/")
        self.pi_dir.setFixedSize(600,height)
        self.pi_browse_btn = QPushButton("Browse")
        self.pi_browse_btn.setFixedSize(50, height)
        self.pi_browse_btn.clicked.connect(self.browse_pi_directory)
        pi_box = QHBoxLayout()
        # pi_box.setContentsMargins(0,10,0,0)
        pi_box.addWidget(pi_dir_lbl)
        pi_box.addWidget(self.pi_dir)
        pi_box.addWidget(self.pi_browse_btn)
        pi_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.begin_btn = QPushButton("Begin")
        self.begin_btn.setFixedSize(size2, height)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedSize(size2, height)
        self.continue_btn = QPushButton("Resume")
        self.continue_btn.setFixedSize(size2, height)
        self.abort_btn = QPushButton("Abort")
        self.abort_btn.setFixedSize(size2, height)

        self.visual_box = ComboBoxWithPlaceholder("view option", exclusive=True)
        # Start with trajectory preview as default
        options = ["trajectory preview"]
        
        # Add CA and PVA options if they are defined in settings
        if self.settings_manager:
            ca_fields = {
                "CA X positioner": "CA X positioner",
                "CA Y positioner": "CA Y positioner",
                "CA spectra": "CA spectra",
                "CA camera": "CA camera"
            }
            pva_fields = {
                "PVA positions": "PVA positions",
                "PVA spectra": "PVA spectra",
                "PVA camera": "PVA camera"
            }
            
            # Add CA fields if defined
            for key, label in ca_fields.items():
                value = self.settings_manager.get_setting(key)
                if value and value.strip():
                    options.append(label)
            
            # Add PVA fields if defined
            for key, label in pva_fields.items():
                value = self.settings_manager.get_setting(key)
                if value and value.strip():
                    options.append(label)
        
        self.visual_box.addItems(options)
        self.visual_box.setFixedWidth(size3)
        self.visual_box.check_selected([1])  # Select first item (trajectory preview)

        c1 = QHBoxLayout()
        c1.addWidget(eta_lbl)
        c1.addWidget(self.eta)
        c1.addWidget(self.begin_btn)
        c1.addWidget(self.pause_btn)
        c1.addWidget(self.continue_btn)
        c1.addWidget(self.abort_btn)
        c1.addWidget(self.visual_box)

        self.message_window = QTextEdit("")
        self.message_window.setFixedSize(700, 300)
        self.message_window.setStyleSheet("background: beige; color: black")
        self.message_window.setReadOnly(True)

        control_layout = QVBoxLayout()
        control_layout.addLayout(pi_box)
        control_layout.addLayout(c1)
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
        self.view_box.setFixedHeight(400)
        combined2.addWidget(self.view_box)

        self.make_pretty()
        self.setLayout(combined2)
    
    def update_view_options(self):
        """Update view options dropdown based on CA and PVA settings"""
        if not self.settings_manager:
            return
        
        # Get current selection to preserve it if possible
        current_selection = None
        try:
            checked_indices = self.visual_box.checked_indices()
            if checked_indices:
                current_items = self.visual_box.get_items()
                if checked_indices[0] <= len(current_items):
                    current_selection = current_items[checked_indices[0] - 1]
        except:
            pass
        
        # Clear existing items
        self.visual_box.clear()
        
        # Start with trajectory preview as default
        options = ["trajectory preview"]
        
        # Add CA and PVA options if they are defined in settings
        ca_fields = {
            "CA X positioner": "CA X positioner",
            "CA Y positioner": "CA Y positioner",
            "CA spectra": "CA spectra",
            "CA camera": "CA camera"
        }
        pva_fields = {
            "PVA positions": "PVA positions",
            "PVA spectra": "PVA spectra",
            "PVA camera": "PVA camera"
        }
        
        # Add CA fields if defined
        for key, label in ca_fields.items():
            value = self.settings_manager.get_setting(key)
            if value and value.strip():
                options.append(label)
        
        # Add PVA fields if defined
        for key, label in pva_fields.items():
            value = self.settings_manager.get_setting(key)
            if value and value.strip():
                options.append(label)
        
        # Add options to dropdown
        self.visual_box.addItems(options)
        
        # Restore previous selection if it still exists, otherwise select trajectory preview
        if current_selection and current_selection in options:
            try:
                index = options.index(current_selection) + 1  # +1 because check_selected uses 1-based indexing
                self.visual_box.check_selected([index])
            except:
                self.visual_box.check_selected([1])  # Default to trajectory preview
        else:
            self.visual_box.check_selected([1])  # Default to trajectory preview

    def browse_pi_directory(self):
        """Open folder selection dialog for PI directory"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select PI Directory",
            self.pi_dir.text() if self.pi_dir.text() != "/" else "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder_path:
            self.pi_dir.setText(folder_path)
            print(f"Selected PI directory: {folder_path}")

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
