from PyQt5 import QtGui
from PyQt5.QtWidgets import QScrollArea, QPushButton, QComboBox, QLCDNumber, QComboBox, QVBoxLayout, QWidget, QWidget, QFrame, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout 

class Setup(QWidget):
    def __init__(self):
        super(Setup, self).__init__()
        self.setupUi()

    def setupUi(self):
        box = QVBoxLayout()
        self.scroll_area()
        box.addWidget(self.scroll)
        self.setLayout(box)

        self.scan_generator.setCheckable(True)
        self.scan_generator.setStyleSheet("background-color : grey")
        self.scan_generator.setChecked(False)
        self.scan_generator.setText("scan record")

    def scroll_area(self):
        item_dict = {} #[type(button, file, path, dropdown), descriptions[idx], choices[idx],defaults[idx]]
        item_dict["load_session"] = [["label", "button"], "load local session", None, None]
        item_dict["qserver"] = [["label", "button"], "connect to queue server", None, None]
        item_dict["scan_generator"] = [["label", "button"], "scan record or profile move", None, None]

        item_dict["scan_device_1"] = [["label","linedit"], "scan device 1", None, ""]
        item_dict["scan_device_2"] = [["label","linedit"], "scan device 2", None, ""]
        item_dict["scan_device_3"] = [["label","linedit"], "scan device 3", None, ""]
        item_dict["scan_device_4"] = [["label","linedit"], "scan device 4", None, ""]
        item_dict["scan_device_5"] = [["label","linedit"], "scan device 5", None, ""]
        item_dict["scan_device_6"] = [["label","linedit"], "scan device 6", None, ""]

        v_box = self.create_widget(item_dict)
        v_box.setSpacing(0)
        v_box.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()  # Widget that contains the collection of Vertical Box
        self.scroll_widget.setLayout(v_box)
        self.scroll.setWidget(self.scroll_widget)
        return

    def create_widget(self, item_dict):
        widgetsizes = [240, 115, 50]
        height = 25
        v_box = QVBoxLayout()
        for i, key in enumerate(item_dict.keys()):
            widget_items = item_dict[key][0]
            attrs = item_dict[key]
            widgetsize = widgetsizes[len(widget_items) - 1]
            line_num = "line_{}".format(i)
            setattr(self, line_num, QHBoxLayout())
            line = self.__dict__[line_num]

            for widget in widget_items:
                if widget == "label":
                    name = key + "_lbl"
                    display = key.replace("_", " ")
                    setattr(self, name, QLabel(key))
                    object = self.__dict__[name]
                    object.setText(display)
                    object.setFixedWidth(widgetsize)
                    object.setToolTip(attrs[1])
                    line.addWidget(object)

                elif widget == "lcd":
                    name = key + "_lcd"
                    setattr(self, name, QLCDNumber())
                    object = self.__dict__[name]
                    object.setFixedWidth(widgetsize)
                    font = QtGui.QFont()
                    font.setBold(False)
                    object.setFont(font)
                    object.setFrameShape(QFrame.Shape.NoFrame)
                    object.setDigitCount(2)
                    object.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
                    object.setProperty("intValue", 10)
                    line.addWidget(object)

                elif widget == "linedit":
                    setattr(self, key, QLineEdit())
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(attrs[3])
                    object.objectName = key
                    line.addWidget(object)

                elif widget == "button":
                    display = key.replace("_", " ")
                    setattr(self, key, QPushButton(key))
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(display)
                    line.addWidget(object)

                elif widget == "file":
                    setattr(self, key, QPushButton(key))
                    object = self.__dict__[key]
                    object.setFixedWidth(widgetsize)
                    object.setText(attrs[3])
                    line.addWidget(object)

                elif widget == "combobox":
                    name = key+"_cbbx"
                    setattr(self, name, QComboBox())
                    object = self.__dict__[name]
                    object.setFixedWidth(widgetsize)
                    object.setToolTip(attrs[1])
                    options = attrs[2]
                    default = attrs[3]
                    for option in options:
                        object.addItem(option)
                    idx = options.index(default)
                    object.setCurrentIndex(idx)
                    line.addWidget(object)

            v_box.addLayout(line)
        return v_box
