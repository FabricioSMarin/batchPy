import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QDialogButtonBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore


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
