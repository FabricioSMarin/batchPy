import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QDialogButtonBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QtCore

class SaveLoad():

    def save_local_session(self):
        session = self.get_session()
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_session.json")
        with open(fname, 'w') as f:
            json.dump(session, f)

    def save_log(self):
        """Save message window content to log file based on PI directory"""
        try:
            # Get current PI directory
            current_pi_dir = self.controls.pi_dir.text()
            if not current_pi_dir:
                print("No PI directory set, cannot save log")
                return
            
            # Get message window content
            message_content = self.controls.message_window.toPlainText()
            if not message_content.strip():
                print("No content in message window to save")
                return
            
            # Create log filename based on PI directory and timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = f"batch_log_{timestamp}.txt"
            log_path = os.path.join(current_pi_dir, log_filename)
            
            # Check if we should append to existing log or create new one
            # Look for existing log files in the PI directory
            existing_logs = []
            if os.path.exists(current_pi_dir):
                for file in os.listdir(current_pi_dir):
                    if file.startswith("batch_log_") and file.endswith(".txt"):
                        existing_logs.append(file)
            
            # If there are existing logs, check if we should append to the most recent one
            # (if it was created today and PI directory hasn't changed)
            should_append = False
            target_log_path = log_path
            
            if existing_logs:
                # Sort by modification time, most recent first
                existing_logs.sort(key=lambda x: os.path.getmtime(os.path.join(current_pi_dir, x)), reverse=True)
                most_recent_log = existing_logs[0]
                most_recent_path = os.path.join(current_pi_dir, most_recent_log)
                
                # Check if the most recent log was created today
                log_mtime = os.path.getmtime(most_recent_path)
                log_date = time.strftime("%Y%m%d", time.localtime(log_mtime))
                today = time.strftime("%Y%m%d")
                
                if log_date == today:
                    # Check if PI directory hasn't changed since last log save
                    # We'll track this by checking if there's a pi_dir_backup.json file
                    current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
                    backup_file = os.path.join(current_dir, "pi_dir_backup.json")
                    
                    if os.path.exists(backup_file):
                        try:
                            with open(backup_file, 'r') as f:
                                backup_data = json.load(f)
                            if backup_data.get('pi_directory') == current_pi_dir:
                                should_append = True
                                target_log_path = most_recent_path
                        except:
                            pass
            
            # Prepare log content with timestamp
            log_header = f"\n{'='*80}\n"
            log_header += f"Log Entry - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            log_header += f"PI Directory: {current_pi_dir}\n"
            log_header += f"{'='*80}\n\n"
            
            # Write to log file
            if should_append:
                # Append to existing log
                with open(target_log_path, 'a', encoding='utf-8') as f:
                    f.write(log_header)
                    f.write(message_content)
                    f.write("\n")
                print(f"Appended message window content to existing log: {target_log_path}")
            else:
                # Create new log file
                with open(target_log_path, 'w', encoding='utf-8') as f:
                    f.write(log_header)
                    f.write(message_content)
                    f.write("\n")
                print(f"Created new log file: {target_log_path}")
                
        except Exception as e:
            print(f"Error saving log: {e}")

    def open_local_session(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = os.path.join(current_dir, "local_session.json")
        session = None
        
        if os.path.exists(fname) and os.path.getsize(fname):
            try:
                with open(fname, 'r') as f:
                    session = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading local session file: {e}")
                print("Creating new session file...")
                # Backup the corrupted file
                backup_fname = fname + ".backup"
                try:
                    os.rename(fname, backup_fname)
                    print(f"Corrupted file backed up as: {backup_fname}")
                except:
                    pass
                session = None
        
        if session is None:
            session = self.get_session()
            try:
                with open(fname, 'w') as f:
                    json.dump(session, f)
            except Exception as e:
                print(f"Error saving new session file: {e}")

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
