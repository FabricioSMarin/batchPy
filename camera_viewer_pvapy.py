#!/usr/bin/env python3
"""
EPICS PVA Camera Viewer (using pvapy)
A PyQt GUI application for viewing camera streams from EPICS PVA using pvapy.
"""

import sys
import numpy as np
import json
import os
import psutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QFrame, QMessageBox, QSizePolicy, QSpinBox)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
import pyqtgraph as pg
from pvapy import Channel
import time

class CameraStreamThread(QThread):
    """Thread for handling EPICS PVA camera stream using pvapy"""
    image_received = pyqtSignal(np.ndarray, float)  # image_data, timestamp
    error_occurred = pyqtSignal(str)
    connection_established = pyqtSignal()
    
    def __init__(self, pv_name):
        super().__init__()
        self.pv_name = pv_name
        self.channel = None
        self.is_running = False
        
    def run(self):
        try:
            print(f"Attempting to connect to PV: {self.pv_name}")
            
            # Create channel using pvapy
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
                    
                    # Handle the specific structure: value is a tuple with (data_dict, type_dict)
                    if 'value' in pv:
                        value = pv['value']
                        print(f"Value field type: {type(value)}")
                        
                        if isinstance(value, tuple) and len(value) >= 1:
                            # First element should contain the actual data
                            data_dict = value[0]
                            print(f"Data dict keys: {list(data_dict.keys()) if isinstance(data_dict, dict) else 'Not a dict'}")
                            
                            # Look for dimension information in the PVA structure
                            image_width = None
                            image_height = None
                            
                            # Check if there are dimension fields in the data dict
                            for dim_field in ['width', 'height', 'imageWidth', 'imageHeight', 'cols', 'rows']:
                                if dim_field in data_dict:
                                    if dim_field in ['width', 'imageWidth', 'cols']:
                                        image_width = data_dict[dim_field]
                                    elif dim_field in ['height', 'imageHeight', 'rows']:
                                        image_height = data_dict[dim_field]
                                    print(f"Found dimension {dim_field}: {data_dict[dim_field]}")
                            
                            # Also check the second element of the tuple for metadata
                            if len(value) > 1:
                                type_dict = value[1]
                                print(f"Type dict: {type_dict}")
                                if isinstance(type_dict, dict):
                                    for key, val in type_dict.items():
                                        print(f"Type info - {key}: {val}")
                            
                            # Look for timestamp information in the PVA structure
                            timestamp = None
                            if 'value' in pv:
                                # Check if there's a timestamp field at the top level
                                for ts_field in ['timeStamp', 'timestamp', 'time', 'epicsTimeStamp']:
                                    if ts_field in pv:
                                        timestamp = pv[ts_field]
                                        print(f"Found timestamp field '{ts_field}': {timestamp}")
                                        break
                                
                                # Check in the data dictionary
                                if timestamp is None and isinstance(data_dict, dict):
                                    for ts_field in ['timeStamp', 'timestamp', 'time', 'epicsTimeStamp']:
                                        if ts_field in data_dict:
                                            timestamp = data_dict[ts_field]
                                            print(f"Found timestamp in data dict '{ts_field}': {timestamp}")
                                            break
                            
                            if isinstance(data_dict, dict) and 'ubyteValue' in data_dict:
                                image_data = data_dict['ubyteValue']
                                print(f"Found ubyteValue: {type(image_data)}")
                                
                                # If we have dimension info, use it
                                if image_width and image_height:
                                    print(f"Using provided dimensions: {image_width}x{image_height}")
                                    if len(image_data) == image_width * image_height:
                                        image_data = image_data.reshape(image_height, image_width)
                                        print(f"Reshaped using provided dimensions: {image_data.shape}")
                                    else:
                                        print(f"Warning: Data length {len(image_data)} doesn't match {image_width}x{image_height}={image_width*image_height}")
                            else:
                                # Try other common field names in the data dict
                                for field_name in ['image', 'data', 'array', 'pixelData', 'value']:
                                    if field_name in data_dict:
                                        image_data = data_dict[field_name]
                                        print(f"Found image data in '{field_name}': {type(image_data)}")
                                        break
                    
                    # Fallback: try other common field names
                    if image_data is None:
                        for field_name in ['image', 'data', 'array', 'pixelData']:
                            if field_name in pv:
                                image_data = pv[field_name]
                                print(f"Found image data in field '{field_name}': {type(image_data)}")
                                break
                    
                    if image_data is None:
                        print("No image data found in PV structure")
                        return
                    
                    # Convert to numpy array if needed
                    if not isinstance(image_data, np.ndarray):
                        image_data = np.array(image_data)
                    
                    print(f"Image data shape: {image_data.shape}")
                    print(f"Image data type: {image_data.dtype}")
                    print(f"Image data range: {image_data.min()} to {image_data.max()}")
                    
                    # Handle different data shapes
                    if len(image_data.shape) == 1:
                        # Try to reshape 1D to 2D
                        side_length = int(np.sqrt(len(image_data)))
                        if side_length * side_length == len(image_data):
                            image_data = image_data.reshape(side_length, side_length)
                            print(f"Reshaped 1D to 2D (square): {image_data.shape}")
                        else:
                            # Calculate all possible factor pairs for the array length
                            total_pixels = len(image_data)
                            factors = []
                            for i in range(1, int(np.sqrt(total_pixels)) + 1):
                                if total_pixels % i == 0:
                                    factors.append((i, total_pixels // i))
                                    if i != total_pixels // i:  # Avoid duplicate square factors
                                        factors.append((total_pixels // i, i))
                            
                            # Sort factors by aspect ratio closeness to common camera ratios
                            def aspect_ratio_score(dim):
                                h, w = dim
                                ratio = h / w
                                # Common camera aspect ratios: 4:3, 16:9, 1:1, 3:2
                                common_ratios = [4/3, 16/9, 1, 3/2]
                                return min(abs(ratio - r) for r in common_ratios)
                            
                            factors.sort(key=aspect_ratio_score)
                            
                            # Try the most likely dimensions first
                            reshaped = False
                            print(f"Available factor pairs: {factors[:10]}")
                            
                            # For your specific camera, let's try different interpretations
                            if total_pixels == 1241632:
                                print(f"Trying different interpretations for 1241632 pixels...")
                                
                                # The "lines shifted to the right" suggests the data might be stored differently
                                # Let's try the most common camera dimensions first
                                
                                # Try 964x1288 first (this might be the correct orientation)
                                image_data = image_data.reshape(964, 1288)
                                print(f"Using 964x1288 (aspect ratio: {964/1288:.3f}) - trying portrait orientation")
                                reshaped = True
                            else:
                                # For other cameras, try the most likely dimensions
                                for h, w in factors[:5]:  # Try top 5 most likely dimensions
                                    if 100 <= h <= 4000 and 100 <= w <= 4000:  # Reasonable camera dimensions
                                        image_data = image_data.reshape(h, w)
                                        print(f"Reshaped to {h}x{w} (aspect ratio: {h/w:.3f})")
                                        reshaped = True
                                        break
                            
                            if not reshaped:
                                print(f"Cannot find reasonable 2D dimensions for {total_pixels} pixels")
                                print(f"Available factors: {factors[:20]}")  # Show first 20 factors
                                return
                    elif len(image_data.shape) == 2:
                        # Already 2D, check if it's reasonable
                        if image_data.shape[0] > 0 and image_data.shape[1] > 0:
                            print(f"Using 2D data as-is: {image_data.shape}")
                        else:
                            print(f"Invalid 2D shape: {image_data.shape}")
                            return
                    elif len(image_data.shape) > 2:
                        # Take first 2D slice if higher dimensional
                        if image_data.shape[0] > 0:
                            image_data = image_data.reshape(image_data.shape[0], -1)
                            print(f"Flattened higher dimensional array to: {image_data.shape}")
                        else:
                            print(f"Invalid higher dimensional shape: {image_data.shape}")
                            return
                    
                    # Create timestamp if none found
                    if timestamp is None:
                        import time
                        timestamp = time.time()
                        print(f"Using system timestamp: {timestamp}")
                    
                    self.image_received.emit(image_data, timestamp)
                    
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
        self.collecting = False
        self.collected_images = []  # Will store dictionaries with 'image' and 'timestamp'
        self.image_counter = 0
        self.settings_file = "camera_viewer_settings.json"
        self.init_ui()
        self.load_settings()
        self.setup_memory_monitor()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("EPICS PVA Camera Viewer (pvapy)")
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
        
        # Add memory monitor to status bar
        self.memory_label = QLabel("Memory: --")
        self.memory_label.setStyleSheet("color: #666; font-size: 10px;")
        self.statusBar().addPermanentWidget(self.memory_label)
        
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
        self.pv_input.setPlaceholderText("e.g., 2idbnpcamA:Pva1:Image")
        self.pv_input.returnPressed.connect(self.start_stream)
        self.pv_input.textChanged.connect(self.on_pv_changed)
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
        
        # Rotation control
        rotation_label = QLabel("Rotate:")
        rotation_label.setMinimumWidth(50)
        layout.addWidget(rotation_label)
        
        self.rotation_spinbox = QSpinBox()
        self.rotation_spinbox.setRange(0, 3)
        self.rotation_spinbox.setValue(0)
        self.rotation_spinbox.setSuffix("×90°")
        self.rotation_spinbox.setMinimumWidth(80)
        self.rotation_spinbox.valueChanged.connect(self.on_rotation_changed)
        layout.addWidget(self.rotation_spinbox)
        
        # Dimension test buttons
        test_dims_button = QPushButton("Test Dims")
        test_dims_button.clicked.connect(self.test_dimensions)
        test_dims_button.setMinimumWidth(80)
        layout.addWidget(test_dims_button)
        
        # Collection controls
        self.collect_button = QPushButton("Start Collect")
        self.collect_button.clicked.connect(self.toggle_collection)
        self.collect_button.setEnabled(False)
        self.collect_button.setMinimumWidth(100)
        layout.addWidget(self.collect_button)
        
        self.discard_button = QPushButton("Discard")
        self.discard_button.clicked.connect(self.discard_images)
        self.discard_button.setEnabled(False)
        self.discard_button.setMinimumWidth(80)
        layout.addWidget(self.discard_button)
        
        # Image counter
        self.counter_label = QLabel("Images: 0")
        self.counter_label.setMinimumWidth(80)
        self.counter_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addWidget(self.counter_label)
        
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
    
    def setup_memory_monitor(self):
        """Setup memory monitoring timer"""
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(2000)  # Update every 2 seconds
        self.update_memory_usage()  # Initial update
    
    def update_memory_usage(self):
        """Update memory usage display"""
        try:
            # Get process memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            
            # Get system memory usage
            system_memory = psutil.virtual_memory()
            system_used_mb = system_memory.used / 1024 / 1024
            system_total_mb = system_memory.total / 1024 / 1024
            system_percent = system_memory.percent
            
            # Update display
            self.memory_label.setText(f"Memory: {memory_mb:.1f}MB | System: {system_percent:.1f}%")
            
            # Change color based on memory usage
            if system_percent > 90:
                self.memory_label.setStyleSheet("color: red; font-size: 10px; font-weight: bold;")
            elif system_percent > 75:
                self.memory_label.setStyleSheet("color: orange; font-size: 10px;")
            else:
                self.memory_label.setStyleSheet("color: #666; font-size: 10px;")
                
        except Exception as e:
            self.memory_label.setText("Memory: Error")
            self.memory_label.setStyleSheet("color: red; font-size: 10px;")
    
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
        self.collect_button.setEnabled(False)  # Will be enabled when connected
        self.discard_button.setEnabled(False)
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
        self.collect_button.setEnabled(False)
        self.discard_button.setEnabled(False)
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Stop collection if active
        self.collecting = False
        self.collect_button.setText("Start Collect")
        
        self.statusBar().showMessage("Stream stopped")
    
    def update_image(self, image_data, timestamp):
        """Update the image display with new data"""
        try:
            # Convert to appropriate format for display
            if image_data.dtype != np.uint8:
                # Normalize to 0-255 range
                image_data = ((image_data - image_data.min()) / 
                            (image_data.max() - image_data.min()) * 255).astype(np.uint8)
            
            # Store the original image data for rotation
            self.current_image_data = image_data
            
            # Collect image if collection is active
            if self.collecting:
                # Store both image and timestamp
                image_entry = {
                    'image': image_data.copy(),
                    'timestamp': timestamp,
                    'frame_number': self.image_counter + 1
                }
                self.collected_images.append(image_entry)
                self.image_counter += 1
                self.counter_label.setText(f"Images: {self.image_counter}")
                
                # Convert timestamp to readable format
                import datetime
                dt = datetime.datetime.fromtimestamp(timestamp)
                readable_time = dt.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
                print(f"Collected image {self.image_counter} at {readable_time}")
            
            # Apply current rotation
            self.apply_rotation()
            
            # Update status
            if self.collecting:
                self.status_label.setText("Connected - Collecting")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            self.handle_error(f"Error updating image: {str(e)}")
    
    def apply_rotation(self):
        """Apply the current rotation setting to the image"""
        if hasattr(self, 'current_image_data'):
            rotation_steps = self.rotation_spinbox.value()
            rotated_data = np.rot90(self.current_image_data, k=rotation_steps)
            self.image_item.setImage(rotated_data, autoLevels=True)
    
    def on_rotation_changed(self):
        """Handle rotation control change"""
        self.apply_rotation()
    
    def test_dimensions(self):
        """Test different dimension interpretations"""
        if hasattr(self, 'current_image_data') and self.current_image_data is not None:
            # Cycle through different dimension interpretations
            if not hasattr(self, 'dimension_index'):
                self.dimension_index = 0
            
            dimensions = [
                (964, 1288),   # Portrait
                (1288, 964),   # Landscape
                (1112, 1116),  # Square-ish
                (736, 1687),   # Very tall
                (644, 1928),   # Very wide
            ]
            
            if self.dimension_index < len(dimensions):
                h, w = dimensions[self.dimension_index]
                try:
                    test_data = self.current_image_data.reshape(h, w)
                    self.current_image_data = test_data
                    self.apply_rotation()
                    print(f"Testing dimensions: {h}x{w}")
                    self.statusBar().showMessage(f"Testing: {h}x{w}")
                    self.dimension_index += 1
                except Exception as e:
                    print(f"Error testing {h}x{w}: {e}")
                    self.dimension_index += 1
            else:
                # Reset to first dimension
                self.dimension_index = 0
                h, w = dimensions[0]
                test_data = self.current_image_data.reshape(h, w)
                self.current_image_data = test_data
                self.apply_rotation()
                print(f"Reset to: {h}x{w}")
                self.statusBar().showMessage(f"Reset to: {h}x{w}")
    
    def on_connection_established(self):
        """Handle successful connection to PV"""
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
        self.status_label.setText("Connected - Waiting for data...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.statusBar().showMessage("Connected to PV - waiting for image data")
        
        # Enable collection controls
        self.collect_button.setEnabled(True)
        self.discard_button.setEnabled(True)
    
    def connection_timeout(self):
        """Handle connection timeout"""
        self.handle_error("Connection timeout - unable to connect to PV within 15 seconds")
    
    def toggle_collection(self):
        """Toggle image collection on/off"""
        if self.collecting:
            # Stop collection
            self.collecting = False
            self.collect_button.setText("Start Collect")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            print(f"Stopped collecting. Total images collected: {self.image_counter}")
            self.statusBar().showMessage(f"Collection stopped - {self.image_counter} images collected")
        else:
            # Start collection
            self.collecting = True
            self.collect_button.setText("Stop Collect")
            self.status_label.setText("Connected - Collecting")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            print("Started collecting images")
            self.statusBar().showMessage("Collection started")
    
    def discard_images(self):
        """Discard all collected images"""
        if self.collected_images:
            discarded_count = len(self.collected_images)
            
            # Show timestamp range before discarding
            if discarded_count > 0:
                first_time = self.collected_images[0]['timestamp']
                last_time = self.collected_images[-1]['timestamp']
                duration = last_time - first_time
                
                import datetime
                first_dt = datetime.datetime.fromtimestamp(first_time)
                last_dt = datetime.datetime.fromtimestamp(last_time)
                
                print(f"Discarding {discarded_count} images:")
                print(f"  First image: {first_dt.strftime('%H:%M:%S.%f')[:-3]}")
                print(f"  Last image:  {last_dt.strftime('%H:%M:%S.%f')[:-3]}")
                print(f"  Duration:    {duration:.3f} seconds")
                print(f"  Frame rate:  {discarded_count/duration:.1f} fps")
            
            self.collected_images.clear()
            self.image_counter = 0
            self.counter_label.setText("Images: 0")
            self.statusBar().showMessage(f"Discarded {discarded_count} images")
        else:
            print("No images to discard")
            self.statusBar().showMessage("No images to discard")
    
    def get_collected_images_info(self):
        """Get information about collected images"""
        if not self.collected_images:
            return "No images collected"
        
        first_time = self.collected_images[0]['timestamp']
        last_time = self.collected_images[-1]['timestamp']
        duration = last_time - first_time
        
        import datetime
        first_dt = datetime.datetime.fromtimestamp(first_time)
        last_dt = datetime.datetime.fromtimestamp(last_time)
        
        info = f"Collected {len(self.collected_images)} images:\n"
        info += f"  First: {first_dt.strftime('%H:%M:%S.%f')[:-3]}\n"
        info += f"  Last:  {last_dt.strftime('%H:%M:%S.%f')[:-3]}\n"
        info += f"  Duration: {duration:.3f} seconds\n"
        info += f"  Frame rate: {len(self.collected_images)/duration:.1f} fps"
        
        return info
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'last_pv_name': self.pv_input.text(),
                'window_geometry': {
                    'x': self.geometry().x(),
                    'y': self.geometry().y(),
                    'width': self.geometry().width(),
                    'height': self.geometry().height()
                },
                'rotation_setting': self.rotation_spinbox.value()
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"Settings saved to {self.settings_file}")
            
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Load PV name
                if 'last_pv_name' in settings and settings['last_pv_name']:
                    self.pv_input.setText(settings['last_pv_name'])
                    print(f"Loaded PV name: {settings['last_pv_name']}")
                
                # Load window geometry
                if 'window_geometry' in settings:
                    geom = settings['window_geometry']
                    self.setGeometry(geom['x'], geom['y'], geom['width'], geom['height'])
                
                # Load rotation setting
                if 'rotation_setting' in settings:
                    self.rotation_spinbox.setValue(settings['rotation_setting'])
                
                print(f"Settings loaded from {self.settings_file}")
            else:
                print(f"No settings file found at {self.settings_file}")
                
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def on_pv_changed(self):
        """Handle PV input text change - save settings"""
        # Save settings when PV is changed (with a small delay to avoid too frequent saves)
        if hasattr(self, '_pv_save_timer'):
            self._pv_save_timer.stop()
        
        self._pv_save_timer = QTimer()
        self._pv_save_timer.timeout.connect(self.save_settings)
        self._pv_save_timer.setSingleShot(True)
        self._pv_save_timer.start(1000)  # Save 1 second after user stops typing
    
    def handle_error(self, error_message):
        """Handle errors from the stream thread"""
        print(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)
        self.stop_stream()
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.stop_stream()
        if hasattr(self, 'memory_timer'):
            self.memory_timer.stop()
        self.save_settings()
        event.accept()

def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("EPICS PVA Camera Viewer (pvapy)")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = CameraViewer()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()