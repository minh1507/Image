import sys
import os
from PySide6.QtWidgets import (QVBoxLayout,
                               QPushButton, 
                               QSlider,
                               QDialog, 
                               QLineEdit)  
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

class AdjustDialog(QDialog):
    def __init__(self, title, slider_min, slider_max, default_value, on_value_changed):
        super().__init__()
        self.setWindowTitle(title)
        self.setModal(False)  

        layout = QVBoxLayout(self)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(slider_min, slider_max)
        self.slider.setValue(default_value)
        self.slider.valueChanged.connect(on_value_changed)
        layout.addWidget(self.slider)

        self.input_field = QLineEdit(self) 
        self.input_field.setValidator(QIntValidator(slider_min, slider_max))  
        self.input_field.setText(str(default_value))
        self.input_field.textChanged.connect(self.on_input_changed) 
        layout.addWidget(self.input_field)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def on_input_changed(self, text):
        if text:
            value = int(text)
            self.slider.setValue(value)  
