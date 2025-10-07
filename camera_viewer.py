#!/usr/bin/env python3
"""
EPICS PVA Camera Viewer
A PyQt GUI application for viewing camera streams from EPICS PVA.
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QFrame, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
import pyqtgraph as pg
from pvaccess import Channel
import time

class CameraStreamThread(QThread):
    """Thread for handling EPICS PVA camera stream"""
    image_received = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    connection_established = pyqtSignal()
    
    def __init__(self, pv_name):
        super().__init__()
        self.pv_name = pv_name
        self.channel = None
        self.is_running = False
        self.connection_timeout = 10  # seconds
        
    def run(self):
        try:
            print(f"Attempting to connect to PV: {self.pv_name}")
            
            # Create channel (timeout not supported in this version)
            self.channel = Channel(self.pv_name)
            
            # Try to get initial data to test connection
            print("Testing connection with get()...")
            initial_data = self.channel.get()
            print(f"Initial data received: {type(initial_data)}")
            print(f"Data keys: {list(initial_data.keys()) if hasattr(initial_data, 'keys') else 'No keys'}")
            
            self.is_running = True
            self.connection_established.emit()
            
            def monitor_callback(pv):
                try:
                    print(f"Received data: {type(pv)}")
                    print(f"PV keys: {list(pv.keys()) if hasattr(pv, 'keys') else 'No keys'}")
                    
                    # Extract image data from PVA structure
                    image_data = None
                    
                    # Try different common field names
                    for field_name in ['value', 'image', 'data', 'array', 'pixelData']:
                        if field_name in pv:
                            image_data = pv[field_name]
                            print(f"Found image data in field '{field_name}': {type(image_data)}")
                            break
                    
                    # If no common field found, try to get the first array field
                    if image_data is None:
                        for key in pv.keys():
                            if isinstance(pv[key], np.ndarray):
                                image_data = pv[key]
                                print(f"Found array data in field '{key}': {image_data.shape}")
                                break
                    
                    if image_data is None:
                        print("No image data found in PV structure")
                        return
                    
                    # Convert to numpy array if needed
                    if not isinstance(image_data, np.ndarray):
                        image_data = np.array(image_data)
                    
                    print(f"Image data shape: {image_data.shape}")
                    
                    # Ensure it's 2D
                    if len(image_data.shape) == 1:
                        # Try to reshape if we know dimensions
                        side_length = int(np.sqrt(len(image_data)))
                        if side_length * side_length == len(image_data):
                            image_data = image_data.reshape(side_length, side_length)
                            print(f"Reshaped to 2D: {image_data.shape}")
                        else:
                            print(f"Cannot reshape 1D array of length {len(image_data)} to square")
                            return
                    elif len(image_data.shape) > 2:
                        # Take first 2D slice if higher dimensional
                        image_data = image_data.reshape(image_data.shape[0], -1)
                        print(f"Flattened higher dimensional array to: {image_data.shape}")
                    
                    self.image_received.emit(image_data)
                    
                except Exception as e:
                    print(f"Error processing image: {str(e)}")
                    self.error_occurred.emit(f"Error processing image: {str(e)}")
            
            # Start monitoring
            print("Starting monitor...")
            self.channel.monitor(monitor_callback)
            
            # Keep thread alive
            while self.is_running:
                self.msleep(100)
                
        except Exception as e:
            error_msg = str(e)
            print(f"Connection error: {error_msg}")
            
            # Provide more helpful error messages
            if "timed out" in error_msg.lower():
                self.error_occurred.emit(f"Connection timeout to PV '{self.pv_name}'. Check:\n"
                                       f"• PV name is correct\n"
                                       f"• EPICS PVA server is running\n"
                                       f"• Network connectivity\n"
                                       f"• Try: python test_pva_connection.py {self.pv_name}")
            elif "not found" in error_msg.lower():
                self.error_occurred.emit(f"PV '{self.pv_name}' not found. Check:\n"
                                       f"• PV name spelling\n"
                                       f"• PV exists on the server\n"
                                       f"• Try: python test_pva_connection.py {self.pv_name}")
            else:
                self.error_occurred.emit(f"Error connecting to PV '{self.pv_name}': {error_msg}")
    
    def stop(self):
        self.is_running = False
        if self.channel:
            try:
                self.channel.stopMonitor()
            except:
                pass
        self.quit()
        self.wait()

class CameraViewer(QMainWindow):
    """Main application window for camera viewer"""
    
    def __init__(self):
        super().__init__()
        self.stream_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("EPICS PVA Camera Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Image display
        self.image_widget = self.create_image_display()
        main_layout.addWidget(self.image_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready - Enter PV name and click Start")
        
    def create_control_panel(self):
        """Create the control panel with PV input and buttons"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # PV input
        pv_label = QLabel("EPICS PV:")
        pv_label.setMinimumWidth(80)
        layout.addWidget(pv_label)
        
        self.pv_input = QLineEdit()
        self.pv_input.setPlaceholderText("e.g., 2idsft:Pva1:Image")
        self.pv_input.returnPressed.connect(self.start_stream)
        layout.addWidget(self.pv_input)
        
        # Buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_stream)
        self.start_button.setMinimumWidth(80)
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_stream)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumWidth(80)
        layout.addWidget(self.stop_button)
        
        # Status label
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        return panel
    
    def create_image_display(self):
        """Create the image display widget"""
        # Create a horizontal layout widget to hold both image and histogram
        from PyQt5.QtWidgets import QHBoxLayout, QWidget
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create GraphicsLayoutWidget for image display
        self.image_widget = pg.GraphicsLayoutWidget()
        
        # Create plot for image display
        self.image_plot = self.image_widget.addPlot(title="Camera Stream")
        self.image_plot.setAspectLocked(True)
        self.image_plot.hideAxis('left')
        self.image_plot.hideAxis('bottom')
        
        # Create ImageItem for displaying the camera image
        self.image_item = pg.ImageItem()
        self.image_plot.addItem(self.image_item)
        
        # Set up histogram for better contrast
        self.histogram = pg.HistogramLUTWidget()
        self.histogram.setImageItem(self.image_item)
        
        # Add both widgets to the horizontal layout
        layout.addWidget(self.image_widget, 1)  # Image takes most space
        layout.addWidget(self.histogram, 0)     # Histogram takes minimal space
        
        return container
    
    def start_stream(self):
        """Start the camera stream"""
        pv_name = self.pv_input.text().strip()
        
        if not pv_name:
            QMessageBox.warning(self, "Warning", "Please enter a PV name")
            return
        
        if self.stream_thread and self.stream_thread.isRunning():
            self.stop_stream()
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.pv_input.setEnabled(False)
        self.status_label.setText("Connecting...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Create and start stream thread
        self.stream_thread = CameraStreamThread(pv_name)
        self.stream_thread.image_received.connect(self.update_image)
        self.stream_thread.error_occurred.connect(self.handle_error)
        self.stream_thread.connection_established.connect(self.on_connection_established)
        self.stream_thread.start()
        
        # Set up connection timeout
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.connection_timeout)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.start(15000)  # 15 second timeout
        
        self.statusBar().showMessage(f"Starting stream for PV: {pv_name}")
    
    def stop_stream(self):
        """Stop the camera stream"""
        if self.stream_thread and self.stream_thread.isRunning():
            self.stream_thread.stop()
            self.stream_thread = None
        
        # Stop connection timer if running
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pv_input.setEnabled(True)
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.statusBar().showMessage("Stream stopped")
    
    def update_image(self, image_data):
        """Update the image display with new data"""
        try:
            # Convert to appropriate format for display
            if image_data.dtype != np.uint8:
                # Normalize to 0-255 range
                image_data = ((image_data - image_data.min()) / 
                            (image_data.max() - image_data.min()) * 255).astype(np.uint8)
            
            # Update the image item
            self.image_item.setImage(image_data, autoLevels=True)
            
            # Update status
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            self.handle_error(f"Error updating image: {str(e)}")
    
    def on_connection_established(self):
        """Handle successful connection to PV"""
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
        self.status_label.setText("Connected - Waiting for data...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.statusBar().showMessage("Connected to PV - waiting for image data")
    
    def connection_timeout(self):
        """Handle connection timeout"""
        self.handle_error("Connection timeout - unable to connect to PV within 15 seconds")
    
    def handle_error(self, error_message):
        """Handle errors from the stream thread"""
        print(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)
        self.stop_stream()
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.stop_stream()
        event.accept()

def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("EPICS PVA Camera Viewer")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = CameraViewer()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()