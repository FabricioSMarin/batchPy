from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QComboBox, QStyledItemDelegate, QStyle, QStyleOptionButton, QStyleOptionComboBox, QListView, QStylePainter
from PyQt5.QtCore import Qt, QPoint, QEvent, QRect
from PyQt5.QtGui import QStandardItem

class ComboBoxWithPlaceholder(QComboBox):
    def __init__(self, placeholder_text, exclusive=False, *args, **kwargs):
        super(ComboBoxWithPlaceholder, self).__init__(*args, **kwargs)
        self.placeholder_text = placeholder_text
        self.exclusive = exclusive
        self.setView(QListView())
        self.setItemDelegate(CheckBoxDelegate(self))
        
        self.addItem(self.placeholder_text)
        self.setCurrentIndex(0)
        self.model().item(0).setEnabled(False)

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)


    def wheelEvent(self, event):
        # Ignore the wheel event to prevent scrolling
        event.ignore()
        
    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        # If no item is selected or all items are unchecked, display placeholder text
        if self.currentIndex() == 0 or all(self.itemData(i, Qt.CheckStateRole) == Qt.Unchecked for i in range(1, self.count())):
            opt.currentText = self.placeholder_text

        painter.drawComplexControl(QStyle.CC_ComboBox, opt)
        painter.drawControl(QStyle.CE_ComboBoxLabel, opt)

    def check_all(self):
        for i in range(1, self.model().rowCount()):
            self.model().item(i).setCheckState(Qt.Checked)

    def uncheck_all(self):
        for i in range(1, self.model().rowCount()):
            self.model().item(i).setCheckState(Qt.Unchecked)

    def item_checked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == QtCore.Qt.Checked
    
    def check_selected(self, selected):
        self.uncheck_all()
        for i in selected:
            item = self.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Checked)
            
    def checked_indices(self):
        checked_indices = []
        for i in range(self.count()):
            if self.item_checked(i):
                checked_indices.append(i)
        return checked_indices

    def checked_names(self):
        checked_items = []
        for i in range(1, self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())
        return checked_items
    
    def get_items(self): 
        items = []
        for i in range(1, self.model().rowCount()):
            items.append(self.model().item(i).text())
        return items

    def clear(self):
        # Remove all items except the first one
        self.model().removeRows(1, self.model().rowCount() - 1)
            

class CheckBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(CheckBoxDelegate, self).__init__(parent)
        self.combo = parent

    def paint(self, painter, option, index):
        item = index.model().itemFromIndex(index)
        if item.isEnabled():
            # Draw the checkbox
            check_box_style_option = QStyleOptionButton()
            if item.checkState() == Qt.Checked:
                check_box_style_option.state |= QStyle.State_On
            else:
                check_box_style_option.state |= QStyle.State_Off

            check_box_style_option.rect = self.getCheckBoxRect(option)

            QApplication.style().drawControl(QStyle.CE_CheckBox, check_box_style_option, painter)

        # Draw the text
        super(CheckBoxDelegate, self).paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            item = model.itemFromIndex(index)
            if item.isEnabled():
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                    if self.combo.exclusive:
                        for i in range(model.rowCount()):
                            if i != index.row():
                                model.item(i).setCheckState(Qt.Unchecked)
        return super(CheckBoxDelegate, self).editorEvent(event, model, option, index)

    def getCheckBoxRect(self, option):
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QPoint(option.rect.x() + 5, option.rect.y() +
                                 (option.rect.height() - check_box_rect.height()) // 2)
        return QRect(check_box_point, check_box_rect.size())