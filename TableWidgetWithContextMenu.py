from PyQt5.QtWidgets import QMenu, QTableWidget, QAction, QLineEdit
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QEvent
from customEnter import KeyPressEater

class TableWidgetWithContextMenu(QTableWidget):
    deleteRowSig = pyqtSignal(int)
    moveRowSig = pyqtSignal(list)
    editedSig = pyqtSignal(list)
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

        # Connect the itemChanged signal to the custom slot
        # self.itemChanged.connect(self.handle_item_changed)
        # keyPressEater = KeyPressEater(self)
        # self.installEventFilter(keyPressEater)

    def show_context_menu(self, pos: QPoint):
        global_pos = self.viewport().mapToGlobal(pos)
        row_index = self.rowAt(pos.y())

        if row_index >= 0:  # Ensure a valid row is clicked
            context_menu = QMenu(self)
            delete_action = QAction("Delete Row", self)
            delete_action.triggered.connect(lambda: self.delete_request(row_index))
            context_menu.addAction(delete_action)
            context_menu.exec_(global_pos)

    def delete_request(self, row_index):
        self.deleteRowSig.emit(row_index)

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


    def get_cell_content(table, row, column_key):
        # Get the column index using the column key (header label)
        column_index = None
        for col in range(table.columnCount()):
            if table.horizontalHeaderItem(col).text() == column_key:
                column_index = col
                break

        if column_index is not None:
            # Get the item in the specified cell
            item = table.item(row, column_index)
            if item:
                return item.text()
        return None
