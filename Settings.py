import os
import json
import epics
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QDialogButtonBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QKeyEvent
from PyQt5 import QtCore


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(800, 400)  # Increased width to accommodate second column
        self.timeout = 0.25  # EPICS connection timeout
        
        # Ensure it's a proper standalone window
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint | 
                           QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        
        # Create the main layout
        layout = QVBoxLayout()
        
        # Create grid layout for settings rows
        grid_layout = QGridLayout()
        
        # Create main settings widgets
        self.settings_widgets = {}
        settings_labels = [
            "Fly Loop 1 PV", "Fly Loop 2 PV", "Fly Loop 3 PV", "Fly Loop 4 PV",
            "Step Loop 1 PV", "Step Loop 2 PV", "Step Loop 3 PV", "Step Loop 4 PV",
            "saveData mount point", "host mount point", "Det 1 mount point", "Det 1 filePath PV", 
            "Det 2 mount point", "Det 2 filePath PV", "Det 3 mount point", "Det 3 filePath PV",
            "Det 4 mount point", "Det 4 filePath PV", "Det 5 mount point", "Det 5 filePath PV",
            "Det 6 mount point", "Det 6 filePath PV", "PI Directory",
            "CA spectra", "CA camera",
            "PVA positions", "PVA spectra", "PVA camera"
        ]
        
        # Add main settings to first column
        for i, label_text in enumerate(settings_labels):
            # Create label
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(150)
            
            # Create line edit
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Enter {label_text.lower()}")
            line_edit.setMinimumWidth(200)
            # Install event filter to prevent Enter from closing dialog
            line_edit.installEventFilter(self)
            
            # Store reference for later access
            self.settings_widgets[label_text] = line_edit
            
            # Add to grid
            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(line_edit, i, 1)
        
        # Add positioner limits as second column
        self.positioner_limits_widgets = {}
        self.positioner_value_labels = {}  # Store labels for displaying actual EPICS values
        positioner_limits = [
            "Positioner 1 PV", "Positioner 1 RBV", "Positioner 1 HLM", "Positioner 1 LLM", "Positioner 1 VMAX", "Positioner 1 VBAS", "Positioner 1 MRES", "Positioner 1 EGU",
            "Positioner 2 PV", "Positioner 2 RBV", "Positioner 2 HLM", "Positioner 2 LLM", "Positioner 2 VMAX", "Positioner 2 VBAS", "Positioner 2 MRES", "Positioner 2 EGU",
            "Positioner 3 PV", "Positioner 3 RBV", "Positioner 3 HLM", "Positioner 3 LLM", "Positioner 3 VMAX", "Positioner 3 VBAS", "Positioner 3 MRES", "Positioner 3 EGU",
            "Positioner 4 PV", "Positioner 4 RBV", "Positioner 4 HLM", "Positioner 4 LLM", "Positioner 4 VMAX", "Positioner 4 VBAS", "Positioner 4 MRES", "Positioner 4 EGU"
        ]
        
        # Add positioner limits to second column (starting from column 2)
        for i, limit_name in enumerate(positioner_limits):
            # Create label for limit name
            limit_label = QLabel(f"{limit_name}:")
            limit_label.setMinimumWidth(120)
            
            # Create line edit for limit value
            limit_edit = QLineEdit()
            limit_edit.setPlaceholderText(f"Enter {limit_name.lower()}")
            limit_edit.setMinimumWidth(150)
            
            # Create label for displaying actual EPICS value
            value_label = QLabel("")
            value_label.setMinimumWidth(100)
            value_label.setStyleSheet("color: blue; font-weight: bold;")
            value_label.setWordWrap(True)
            
            # Create unit label (empty for now, can be populated based on limit type)
            unit_label = QLabel("")
            unit_label.setMinimumWidth(50)
            
            # Store references for later access
            self.positioner_limits_widgets[limit_name] = limit_edit
            self.positioner_value_labels[limit_name] = value_label
            
            # Connect returnPressed signal for positioner PV fields
            if limit_name.endswith(" PV"):
                # For PV fields, connect returnPressed to update value
                # Use a lambda with default arguments to capture the correct values
                limit_edit.returnPressed.connect(
                    lambda le=limit_edit, key=limit_name: self.update_positioner_pv_value(le, key)
                )
            else:
                # For non-PV fields, install event filter to prevent Enter from closing dialog
                limit_edit.installEventFilter(self)
            
            # Add to grid (column 2, 3, 4, 5)
            grid_layout.addWidget(limit_label, i, 2)
            grid_layout.addWidget(limit_edit, i, 3)
            grid_layout.addWidget(value_label, i, 4)
            grid_layout.addWidget(unit_label, i, 5)
        
        # Add some spacing
        grid_layout.setSpacing(10)
        grid_layout.setColumnMinimumWidth(0, 150)  # Main settings labels
        grid_layout.setColumnMinimumWidth(1, 200)  # Main settings values
        grid_layout.setColumnMinimumWidth(2, 120)  # Positioner limits labels
        grid_layout.setColumnMinimumWidth(3, 150)  # Positioner limits values
        grid_layout.setColumnMinimumWidth(4, 100)  # EPICS value labels
        grid_layout.setColumnMinimumWidth(5, 50)   # Unit labels
        
        # Add grid to main layout
        layout.addLayout(grid_layout)
        
        # Add refresh button for EPICS values
        refresh_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh EPICS Values")
        refresh_button.clicked.connect(self.refresh_epics_values)
        refresh_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; padding: 8px; border-radius: 4px; }")
        refresh_layout.addWidget(refresh_button)
        refresh_layout.addStretch()  # Push button to the left
        layout.addLayout(refresh_layout)
        
        # Add button box with OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        # Disable default button behavior to prevent Enter from closing dialog
        button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        button_box.button(QDialogButtonBox.Ok).setDefault(False)
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
                
                # Apply loaded settings to main widgets
                for key, value in settings_data.items():
                    if key in self.settings_widgets:
                        self.settings_widgets[key].setText(str(value))
                    elif key in self.positioner_limits_widgets:
                        self.positioner_limits_widgets[key].setText(str(value))
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            settings_data = {}
            
            # Save main settings
            for key, widget in self.settings_widgets.items():
                settings_data[key] = widget.text()
            
            # Save positioner limits
            for key, widget in self.positioner_limits_widgets.items():
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
    
    def update_positioner_values(self, positioner_limits, is_fallback=False):
        """Update the value labels with actual EPICS values or fallback values"""
        for key, value in positioner_limits.items():
            if key in self.positioner_value_labels:
                # Get the PV name from the corresponding line edit
                pv_name = self.positioner_limits_widgets[key].text() if key in self.positioner_limits_widgets else "Unknown PV"
                
                if value is not None:
                    # Format the value for display
                    if isinstance(value, (int, float)):
                        if abs(value) < 0.001 or abs(value) > 1000000:
                            # Use scientific notation for very small or large numbers
                            formatted_value = f"{value:.2e}"
                        else:
                            # Use regular decimal notation
                            formatted_value = f"{value:.6g}"
                    else:
                        formatted_value = str(value)
                    
                    # Add fallback indicator if applicable
                    display_text = formatted_value
                    if is_fallback:
                        display_text = f"{formatted_value} (fallback)"
                        # Change color to orange for fallback values
                        self.positioner_value_labels[key].setStyleSheet("color: orange; font-weight: bold;")
                    else:
                        # Use blue for live EPICS values
                        self.positioner_value_labels[key].setStyleSheet("color: blue; font-weight: bold;")
                    
                    self.positioner_value_labels[key].setText(display_text)
                    
                    # Update tooltip with appropriate message
                    if is_fallback:
                        self.positioner_value_labels[key].setToolTip(f"PV: {pv_name}\nFallback value: {formatted_value}\n(EPICS connection unavailable)")
                    else:
                        self.positioner_value_labels[key].setToolTip(f"PV: {pv_name}\nCurrent value: {formatted_value}")
                else:
                    self.positioner_value_labels[key].setText("N/A")
                    self.positioner_value_labels[key].setStyleSheet("color: red; font-weight: bold;")
                    self.positioner_value_labels[key].setToolTip(f"PV: {pv_name}\nCould not retrieve value from EPICS or fallback")
    
    def clear_positioner_values(self):
        """Clear all positioner value labels"""
        for label in self.positioner_value_labels.values():
            label.setText("")
            label.setToolTip("")
    
    def refresh_epics_values(self):
        """Refresh EPICS values by calling caget on all defined PVs"""
        try:
            print("Refreshing EPICS values...")
            
            # Load fallback values if available
            fallback_values = {}
            if hasattr(self.parent(), 'load_fallback_values'):
                fallback_values = self.parent().load_fallback_values()
            
            # Dictionary to track which values came from EPICS vs fallback
            epics_values = {}
            fallback_used = {}
            
            # Iterate through all positioner limit widgets
            for key, line_edit in self.positioner_limits_widgets.items():
                pv_name = line_edit.text().strip()
                
                if not pv_name:
                    # No PV name entered, skip
                    continue
                
                # Try to get value from EPICS
                try:
                    value = epics.caget(pv_name, connection_timeout=self.timeout)
                    if value is not None:
                        # Successfully got value from EPICS
                        epics_values[key] = value
                        fallback_used[key] = False
                        print(f"{key}: {pv_name} = {value} (EPICS)")
                    else:
                        # EPICS returned None, try fallback
                        if key in fallback_values:
                            epics_values[key] = fallback_values[key]
                            fallback_used[key] = True
                            print(f"{key}: {pv_name} = {fallback_values[key]} (fallback - EPICS returned None)")
                        else:
                            epics_values[key] = None
                            fallback_used[key] = False
                            print(f"{key}: {pv_name} = None (no fallback available)")
                except Exception as e:
                    # EPICS connection failed, try fallback
                    if key in fallback_values:
                        epics_values[key] = fallback_values[key]
                        fallback_used[key] = True
                        print(f"{key}: {pv_name} = {fallback_values[key]} (fallback - EPICS error: {e})")
                    else:
                        epics_values[key] = None
                        fallback_used[key] = False
                        print(f"{key}: {pv_name} = None (EPICS error: {e}, no fallback)")
            
            # Update value labels with proper color coding
            for key, value in epics_values.items():
                if key in self.positioner_value_labels:
                    value_label = self.positioner_value_labels[key]
                    pv_name = self.positioner_limits_widgets[key].text().strip() if key in self.positioner_limits_widgets else "Unknown PV"
                    
                    if value is not None:
                        # Format the value for display
                        if isinstance(value, (int, float)):
                            if abs(value) < 0.001 or abs(value) > 1000000:
                                formatted_value = f"{value:.2e}"
                            else:
                                formatted_value = f"{value:.6g}"
                        else:
                            formatted_value = str(value)
                        
                        # Set color based on whether it's from EPICS or fallback
                        if fallback_used.get(key, False):
                            # Orange for fallback values
                            value_label.setStyleSheet("color: orange; font-weight: bold;")
                            value_label.setText(f"{formatted_value} (fallback)")
                            value_label.setToolTip(f"PV: {pv_name}\nFallback value: {formatted_value}\n(EPICS connection unavailable)")
                        else:
                            # Blue for successful EPICS values
                            value_label.setStyleSheet("color: blue; font-weight: bold;")
                            value_label.setText(formatted_value)
                            value_label.setToolTip(f"PV: {pv_name}\nCurrent value: {formatted_value}")
                    else:
                        # No value available
                        value_label.setText("N/A")
                        value_label.setStyleSheet("color: red; font-weight: bold;")
                        value_label.setToolTip(f"PV: {pv_name}\nCould not retrieve value from EPICS or fallback")
            
            print("EPICS values refreshed successfully")
        except Exception as e:
            print(f"Error refreshing EPICS values: {e}")
            self.clear_positioner_values()
    
    def eventFilter(self, obj, event):
        """Event filter to prevent Enter key from closing dialog when pressed in line edits"""
        if isinstance(obj, QLineEdit) and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Block Enter key for all line edits with event filter (non-PV fields)
                # PV fields don't have event filter installed, so returnPressed will fire normally
                return True  # Event handled, don't propagate
        # For all other events, use default behavior
        return super().eventFilter(obj, event)
    
    def update_positioner_pv_value(self, line_edit, setting_key):
        """Attempt to get PV value using caget and update the value label"""
        try:
            pv_name = line_edit.text().strip()
            if not pv_name:
                print(f"No PV name entered for {setting_key}")
                return
            
            print(f"update_positioner_pv_value called for {setting_key}, PV: {pv_name}")
            value = epics.caget(pv_name, connection_timeout=self.timeout)
            
            if value is not None:
                # Find the corresponding value label and update it
                # The value label key should match the setting key
                if setting_key in self.positioner_value_labels:
                    value_label = self.positioner_value_labels[setting_key]
                    # Format the value for display
                    if isinstance(value, (int, float)):
                        if abs(value) < 0.001 or abs(value) > 1000000:
                            formatted_value = f"{value:.2e}"
                        else:
                            formatted_value = f"{value:.6g}"
                    else:
                        formatted_value = str(value)
                    
                    value_label.setText(formatted_value)
                    value_label.setStyleSheet("color: blue; font-weight: bold;")
                    value_label.setToolTip(f"PV: {pv_name}\nCurrent value: {formatted_value}")
                    print(f"Updated {setting_key} value label with: {formatted_value} (blue - EPICS)")
                else:
                    print(f"No value label found for {setting_key}")
            else:
                print(f"Could not retrieve value from PV: {pv_name}")
                # Try to get fallback value
                fallback_value = None
                if hasattr(self.parent(), 'load_fallback_values'):
                    fallback_values = self.parent().load_fallback_values()
                    if setting_key in fallback_values:
                        fallback_value = fallback_values[setting_key]
                
                # Update value label
                if setting_key in self.positioner_value_labels:
                    value_label = self.positioner_value_labels[setting_key]
                    if fallback_value is not None:
                        # Show fallback value in orange
                        if isinstance(fallback_value, (int, float)):
                            if abs(fallback_value) < 0.001 or abs(fallback_value) > 1000000:
                                formatted_value = f"{fallback_value:.2e}"
                            else:
                                formatted_value = f"{fallback_value:.6g}"
                        else:
                            formatted_value = str(fallback_value)
                        value_label.setText(f"{formatted_value} (fallback)")
                        value_label.setStyleSheet("color: orange; font-weight: bold;")
                        value_label.setToolTip(f"PV: {pv_name}\nFallback value: {formatted_value}\n(EPICS connection unavailable)")
                        print(f"Updated {setting_key} value label with: {formatted_value} (orange - fallback)")
                    else:
                        value_label.setText("N/A")
                        value_label.setStyleSheet("color: red; font-weight: bold;")
                        value_label.setToolTip(f"PV: {pv_name}\nCould not retrieve value")
                        print(f"Updated {setting_key} value label with: N/A (red - no value)")
        except Exception as e:
            print(f"Error getting PV value for {setting_key}: {e}")
            # Update value label to show error
            if setting_key in self.positioner_value_labels:
                value_label = self.positioner_value_labels[setting_key]
                # Try fallback
                fallback_value = None
                if hasattr(self.parent(), 'load_fallback_values'):
                    fallback_values = self.parent().load_fallback_values()
                    if setting_key in fallback_values:
                        fallback_value = fallback_values[setting_key]
                
                if fallback_value is not None:
                    if isinstance(fallback_value, (int, float)):
                        if abs(fallback_value) < 0.001 or abs(fallback_value) > 1000000:
                            formatted_value = f"{fallback_value:.2e}"
                        else:
                            formatted_value = f"{fallback_value:.6g}"
                    else:
                        formatted_value = str(fallback_value)
                    value_label.setText(f"{formatted_value} (fallback)")
                    value_label.setStyleSheet("color: orange; font-weight: bold;")
                    value_label.setToolTip(f"PV: {pv_name}\nFallback value: {formatted_value}\n(EPICS error: {str(e)})")
                else:
                    value_label.setText("Error")
                    value_label.setStyleSheet("color: red; font-weight: bold;")
                    value_label.setToolTip(f"Error: {str(e)}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Override keyPressEvent to prevent Enter key from closing the dialog"""
        # If Enter or Return is pressed, check if it's in a PV field
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Check if focus is on a positioner PV field
            focused_widget = self.focusWidget()
            if isinstance(focused_widget, QLineEdit):
                # Check if this is a positioner PV field
                is_positioner_pv = False
                for key, widget in self.positioner_limits_widgets.items():
                    if widget == focused_widget and key.endswith(" PV"):
                        is_positioner_pv = True
                        break
                
                if is_positioner_pv:
                    # For PV fields, let the returnPressed signal handle it
                    # Don't block it, but prevent dialog from closing
                    event.accept()
                    # Let the line edit process it (so returnPressed fires)
                    focused_widget.keyPressEvent(event)
                    return
                else:
                    # For non-PV fields, ignore Enter to prevent dialog from closing
                    event.ignore()
                    return
            else:
                # Not in a line edit, ignore Enter to prevent dialog from closing
                event.ignore()
                return
        # For all other keys, use default behavior
        super().keyPressEvent(event)

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
    
    def get_positioner_limit(self, key):
        """Get a positioner limit value by key"""
        return self.settings_data.get(key, "")

    def get_positioner_limits(self):
        """Get positioner limits from settings"""
        positioner_limits = {}
        for key, value in self.settings_data.items():
            if key.startswith("Positioner "):
                positioner_limits[key] = value
        return positioner_limits