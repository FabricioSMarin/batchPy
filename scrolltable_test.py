import sys
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QScrollArea

def create_table_widget(n, m):
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('PyQt5 Table Widget')
    
    layout = QVBoxLayout()
    
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    
    table_widget = QTableWidget()
    table_widget.setRowCount(m)
    table_widget.setColumnCount(n)
    
    # Optional: Add headers (for clarity)
    table_widget.setHorizontalHeaderLabels([f'Column {i+1}' for i in range(n)])
    table_widget.setVerticalHeaderLabels([f'Row {i+1}' for i in range(m)])
    
    scroll_area.setWidget(table_widget)
    layout.addWidget(scroll_area)
    
    window.setLayout(layout)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    n = 5  # Number of columns
    m = 10  # Number of rows
    create_table_widget(n, m)
