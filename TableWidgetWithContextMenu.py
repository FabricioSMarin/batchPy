from PyQt5.QtWidgets import QMenu, QTableWidget, QAction, QLineEdit, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QEvent

class TableWidgetWithContextMenu(QTableWidget):
    deleteRowSig = pyqtSignal(list)  # Changed to emit list of row indices
    moveRowSig = pyqtSignal(list)
    editedSig = pyqtSignal(list)
    setLineActionSig = pyqtSignal(list, str)  # Emit list of row indices and action value
    
    def __init__(self, *args, **kwargs):
        super(TableWidgetWithContextMenu, self).__init__(*args, **kwargs)
        # Enable drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setDragDropMode(QTableWidget.InternalMove)
        
        # Enable custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos: QPoint):
        global_pos = self.viewport().mapToGlobal(pos)
        row_index = self.rowAt(pos.y())

        context_menu = QMenu(self)
        
        # Get selected rows
        selected_rows = set()
        for item in self.selectedItems():
            selected_rows.add(item.row())
        
        # If no rows are selected but we clicked on a valid row, select that row
        if len(selected_rows) == 0 and row_index >= 0:
            selected_rows.add(row_index)
        
        if len(selected_rows) > 0:  # Ensure at least one row is selected
            # Determine delete action text based on selection count
            if len(selected_rows) > 1:
                delete_text = f"Delete Row(s) ({len(selected_rows)})"
            else:
                delete_text = "Delete Row"
            
            delete_action = QAction(delete_text, self)
            # Sort rows in descending order for safe deletion
            sorted_rows = sorted(selected_rows, reverse=True)
            delete_action.triggered.connect(lambda: self.delete_request(sorted_rows))
            context_menu.addAction(delete_action)
            
            # Add separator before line action options
            context_menu.addSeparator()
            
            # Add line action options
            sorted_rows_list = sorted(list(selected_rows))
            skip_action = QAction("Set to Skip", self)
            skip_action.triggered.connect(lambda: self.set_line_action(sorted_rows_list, "skip"))
            context_menu.addAction(skip_action)
            
            pause_action = QAction("Set to Pause", self)
            pause_action.triggered.connect(lambda: self.set_line_action(sorted_rows_list, "pause"))
            context_menu.addAction(pause_action)
            
            normal_action = QAction("Set to Normal", self)
            normal_action.triggered.connect(lambda: self.set_line_action(sorted_rows_list, "normal"))
            context_menu.addAction(normal_action)
            
            context_menu.addSeparator()
        
        # Add "Hide Empty Columns" action to the context menu
        hide_empty_columns_action = QAction("Hide Empty Columns", self)
        hide_empty_columns_action.triggered.connect(self.hide_empty_columns)
        context_menu.addAction(hide_empty_columns_action)
        
        # Add "Show Hidden Columns" action to the context menu
        show_hidden_columns_action = QAction("Show Hidden Columns", self)
        show_hidden_columns_action.triggered.connect(self.show_hidden_columns)
        context_menu.addAction(show_hidden_columns_action)
        
        context_menu.exec_(global_pos)

    def hide_empty_columns(self):
        # Iterate over all columns
        for col in range(self.columnCount()):
            is_empty = all(
                not self.item(row, col) or not self.item(row, col).text().strip()
                for row in range(self.rowCount())
            )
            if is_empty:
                self.setColumnHidden(col, True)

    def show_hidden_columns(self):
        # Iterate over all columns and show them
        for col in range(self.columnCount()):
            self.setColumnHidden(col, False)

    def delete_request(self, row_indices):
        # Emit list of row indices (sorted in descending order for safe deletion)
        self.deleteRowSig.emit(row_indices)
    
    def set_line_action(self, row_indices, action_value):
        # Emit list of row indices and the action value to set
        self.setLineActionSig.emit(row_indices, action_value)

    def dropEvent(self, event):
        # Get the index of the dragged row
        dragged_row = self.currentRow()
        
        # Get the index of the target row where the item is dropped
        drop_row = self.rowAt(event.pos().y())
        if drop_row == -1:
            drop_row = self.rowCount() - 1

        if drop_row == dragged_row:
            return

        # Insert a new row at the drop position
        self.insertRow(drop_row)

        # Copy items from the dragged row to the new row
        for column in range(self.columnCount()):
            self.setItem(drop_row, column, self.takeItem(dragged_row + (1 if drop_row < dragged_row else 0), column))

        # Remove the original dragged row
        self.removeRow(dragged_row + (1 if drop_row < dragged_row else 0))
        self.moveRowSig.emit([dragged_row, drop_row])
        event.accept()

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_row = self.currentRow()
            current_col = self.currentColumn()

            # Get the editor widget (QLineEdit) being used for editing the current item
            editor = self.indexWidget(self.model().index(current_row, current_col))
            if isinstance(editor, QLineEdit):
                current_text = editor.text()
            else:
                current_text = self.currentItem().text() if self.currentItem() else "No item selected"
            
            column_header = self.horizontalHeaderItem(current_col).text() if self.horizontalHeaderItem(current_col) else "No header"
            
            print(f"Return/Enter pressed while editing row {current_row}, column {current_col}")
            print(f"Cell contents: {current_text}")
            print(f"Column header: {column_header}")
            self.editedSig.emit([current_row, column_header, current_text])

    def get_cell_content(self, row, column_key):
        # Get the column index using the column key (header label)
        column_index = None
        for col in range(self.columnCount()):
            if self.horizontalHeaderItem(col).text() == column_key:
                column_index = col
                break

        if column_index is not None:
            # Get the item in the specified cell
            item = self.item(row, column_index)
            if item:
                return item.text()
        return None