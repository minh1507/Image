import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QMenu, QFileDialog, 
                               QPushButton, QGraphicsView, 
                               QGraphicsScene, QFrame, QToolTip, 
                               QGraphicsPixmapItem, QDialog, QGridLayout)  
from PySide6.QtGui import QAction, QPixmap, QIcon, QFont
from PySide6.QtCore import Qt, QSize, QRectF
from PIL import Image, ImageEnhance, ImageFilter
from PIL.ImageQt import ImageQt  
from component.crop import CropItem
from component.resize import ResizablePixmapItem
from component.adjust import AdjustDialog

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photoshop-like App")
        self.setGeometry(100, 100, 1200, 800)

        self.current_contrast = 50  
        self.current_brightness = 50 
        self.current_saturation = 50  
        self.current_sharpening = 50 
        self.rotation_angle = 0 
        self.current_pixmap = None 
        self.original_image = None  
        self.flipped_image = None  
        self.is_flipped = False  
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D2D;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #3A3A3A;
            }
            QMenuBar {
                background-color: #333;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #444;
            }
            QMenu {
                background-color: #333;
                color: white;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #777;
            }
            QSlider::handle:horizontal {
                background: #555;
                width: 15px;
            }
            QToolTip { 
                color: black;
                border: 1px solid #444;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setSpacing(0)

        self.create_left_sidebar(main_layout)

        self.create_image_board(main_layout)

        self.create_right_sidebar(main_layout)

        self.create_menu_bar()

        self.current_pixmap = None 

    def create_left_sidebar(self, layout):
        left_sidebar = QVBoxLayout()
        left_sidebar.setContentsMargins(0, 0, 0, 0)
        left_sidebar.setSpacing(0)

        icon_path = os.path.join(os.path.dirname(__file__), 'asset')

        tools = [
            ("Move Tool", os.path.join(icon_path, "move.png"), "Move"),
        ]

        QToolTip.setFont(QFont('SansSerif', 10))

        self.tool_buttons = []

        for tool, icon, description in tools:
            button = QPushButton()
            button.setIcon(QIcon(icon))
            button.setCheckable(True)
            button.setFixedSize(40, 40)
            button.setToolTip(description)
            button.setIconSize(QSize(15, 15))
            button.setCursor(Qt.PointingHandCursor)

            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 0px;
                    margin: 0px;
                    background-color: none;
                    border-radius: 0px;
                }
                QPushButton:focus {
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #87CEEB;
                }
                QPushButton:checked {
                    background-color: #4169E1;
                }
            """)

            button.clicked.connect(lambda checked, b=button: self.on_tool_button_clicked(b))

            left_sidebar.addWidget(button)
            self.tool_buttons.append(button)

        frame = QFrame()
        frame.setLayout(left_sidebar)

        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet("background-color: #E7F3FF;")

        left_sidebar.addStretch()
        layout.addWidget(frame)

    def on_tool_button_clicked(self, clicked_button):
        for button in self.tool_buttons:
            if button != clicked_button: 
                button.setChecked(False)

        if clicked_button.toolTip() == "Resize":
            self.graphics_view.setCursor(Qt.SizeFDiagCursor)
        else:
            self.graphics_view.setCursor(Qt.ArrowCursor)

    def create_image_board(self, layout):
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setAlignment(Qt.AlignCenter)
        self.graphics_view.setStyleSheet("background-color: #5A5A5A;") 
        layout.addWidget(self.graphics_view)

    def create_right_sidebar(self, layout):
        right_sidebar = QVBoxLayout()
        right_sidebar.setContentsMargins(10, 10, 10, 10)
        feature_grid = QGridLayout()
        feature_grid.setSpacing(10)

        features = [
            ("Contrast", self.show_contrast_popup),
            ("Brightness", self.show_brightness_popup),
            ("Saturation", self.show_saturation_popup),
            ("Grayscale", self.convert_to_grayscale),
            ("Flip", self.show_flip_dialog),  
            ("Rotate", self.show_rotate_dialog),
            ("Crop", self.show_crop_dialog), 
            ("Reset", self.reset_image) ,
            ("Sharpen", self.show_sharpen_popup)
        ]

        for i, (feature_name, handler) in enumerate(features):
            button = QPushButton(feature_name)
            button.clicked.connect(handler)
            feature_grid.addWidget(button, i // 2, i % 2)

        right_sidebar.addLayout(feature_grid)
        right_sidebar.addStretch()
        layout.addLayout(right_sidebar)

    def reset_image(self):
        """Reset the image to its original state."""
        if self.original_image is not None:
            self.update_image(self.original_image)  # Use the original image for resetting
            # Reset enhancement values to default
            self.current_contrast = 50
            self.current_brightness = 50
            self.current_saturation = 50
            self.current_sharpening = 50 
            # Reset sliders in dialogs if they exist
            if hasattr(self, 'contrast_dialog'):
                self.contrast_dialog.slider.setValue(self.current_contrast)
            if hasattr(self, 'brightness_dialog'):
                self.brightness_dialog.slider.setValue(self.current_brightness)
            if hasattr(self, 'saturation_dialog'):
                self.saturation_dialog.slider.setValue(self.current_saturation)

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        import_action = QAction("Import Image", self)
        import_action.triggered.connect(self.import_image)
        file_menu.addAction(import_action)

        export_menu = QMenu("Export", self)
        
        self.export_jpg_action = QAction("JPG", self)
        self.export_jpg_action.setEnabled(False)  
        self.export_jpg_action.triggered.connect(lambda: self.export_image("jpg"))
        export_menu.addAction(self.export_jpg_action)

        self.export_png_action = QAction("PNG", self)
        self.export_png_action.setEnabled(False)  
        self.export_png_action.triggered.connect(lambda: self.export_image("png"))
        export_menu.addAction(self.export_png_action)

        file_menu.addMenu(export_menu)

        settings_menu = menubar.addMenu("Settings")

    def show_contrast_popup(self):
        self.contrast_dialog = AdjustDialog("Adjust Contrast", 0, 100, self.current_contrast, self.on_contrast_value_changed)
        self.contrast_dialog.show()

    def show_brightness_popup(self):
        self.brightness_dialog = AdjustDialog("Adjust Brightness", 0, 100, self.current_brightness, self.on_brightness_value_changed)
        self.brightness_dialog.show()

    def show_saturation_popup(self):
        self.saturation_dialog = AdjustDialog("Adjust Saturation", 0, 100, self.current_saturation, self.on_saturation_value_changed)
        self.saturation_dialog.show()

    def show_sharpen_popup(self):
        """Open a dialog to adjust sharpening amount."""
        self.sharpen_dialog = AdjustDialog("Adjust Sharpening", 0, 100, self.current_sharpening, self.on_sharpen_value_changed)
        self.sharpen_dialog.show()

    def on_sharpen_value_changed(self, value):
        self.sharpen_dialog.input_field.setText(str(value))

        if self.current_pixmap is not None:
            q_image = self.current_pixmap.toqimage()
            pil_image = Image.frombytes("RGBA", (q_image.width(), q_image.height()),
                                        q_image.bits(), "raw", "BGRA", 0, 1)

            enhancer = ImageEnhance.Sharpness(self.original_image)

            scale_factor = (value - 50) / 50.0 + 1.0

            scale_factor = max(0.0, min(scale_factor, 2.0))

            sharpened_image = enhancer.enhance(scale_factor)

            self.update_image(sharpened_image)
            self.current_pixmap = sharpened_image  
            self.current_sharpening = value  
            
    def show_crop_dialog(self):
        self.crop_item = CropItem()
        self.graphics_scene.addItem(self.crop_item)
        self.graphics_view.setScene(self.graphics_scene)
        self.crop_item.setRect(QRectF(50, 50, 100, 100))  
        self.crop_item.update_resize_handle_position()

        confirm_button = QPushButton("Confirm Crop")
        confirm_button.clicked.connect(self.confirm_crop)

        cancel_button = QPushButton("Cancel Crop")
        cancel_button.clicked.connect(self.cancel_crop)

        self.graphics_scene.addItem(QGraphicsPixmapItem(self.current_pixmap))  

        self.graphics_view.setScene(self.graphics_scene)  

        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)

        confirm_button.setGeometry(QRectF(10, 10, 100, 30))
        cancel_button.setGeometry(QRectF(120, 10, 100, 30))
    
    def confirm_crop(self):
        if self.original_image and self.crop_item:
            rect = self.crop_item.rect().toRect()
            cropped_image = self.original_image.crop((rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height()))
            self.original_image = cropped_image
            self.update_image_display()
            self.graphics_scene.removeItem(self.crop_item)

    def cancel_crop(self):
        if self.crop_item:
            self.graphics_scene.removeItem(self.crop_item)

    def show_flip_dialog(self):
        flip_popup = QDialog(self)
        flip_popup.setWindowTitle("Flip Image")
        flip_popup.setGeometry(300, 300, 200, 150)
        layout = QVBoxLayout()

        flip_horizontal_button = QPushButton("Flip Horizontal")
        flip_horizontal_button.clicked.connect(lambda: self.apply_flip("horizontal"))
        layout.addWidget(flip_horizontal_button)

        flip_vertical_button = QPushButton("Flip Vertical")
        flip_vertical_button.clicked.connect(lambda: self.apply_flip("vertical"))
        layout.addWidget(flip_vertical_button)

        flip_popup.setLayout(layout)
        flip_popup.exec()  

    def show_rotate_dialog(self):
        rotate_popup = QDialog(self)
        rotate_popup.setWindowTitle("Rotate Image")
        rotate_popup.setGeometry(300, 300, 200, 150)
        layout = QVBoxLayout()

        rotate_left_button = QPushButton("Rotate Left 90°")
        rotate_left_button.clicked.connect(lambda: self.apply_rotate("left"))
        layout.addWidget(rotate_left_button)

        rotate_right_button = QPushButton("Rotate Right 90°")
        rotate_right_button.clicked.connect(lambda: self.apply_rotate("right"))
        layout.addWidget(rotate_right_button)

        rotate_popup.setLayout(layout)
        rotate_popup.exec_()  

    def apply_flip(self, direction):
        if self.current_pixmap is not None:
            q_image = self.current_pixmap.toqimage()  
            pil_image = Image.frombytes("RGBA", (q_image.width(), q_image.height()), 
                                         q_image.bits(), "raw", "BGRA", 0, 1)

            if not self.is_flipped:
                self.original_image = pil_image

                if direction == "horizontal":
                    self.flipped_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                elif direction == "vertical":
                    self.flipped_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)

                self.update_image(self.flipped_image)  
            else:
                self.update_image(self.original_image)  
            
            self.is_flipped = not self.is_flipped

    def apply_rotate(self, direction):
        if self.current_pixmap is not None:
            if direction == "left":
                self.rotation_angle -= 90 
            elif direction == "right":
                self.rotation_angle += 90  

            self.rotation_angle %= 360  

            transformed_image = self.current_pixmap.rotate(self.rotation_angle, expand=True)
            self.update_image(transformed_image)

    def crop_image(self):
        if self.current_pixmap is not None:
            width, height = self.current_pixmap.size
            left = width // 4
            top = height // 4
            right = width * 3 // 4
            bottom = height * 3 // 4

            self.current_pixmap = self.current_pixmap.crop((left, top, right, bottom))
            self.update_image(self.current_pixmap)
        
    def convert_to_grayscale(self):
        if self.current_pixmap is not None:
            gray_image = self.current_pixmap.convert("L")  
            self.update_image(gray_image)

    def on_contrast_value_changed(self, value):
        self.contrast_dialog.input_field.setText(str(value))  
        if self.current_pixmap is not None:
            if hasattr(self, 'original_pixmap'):
                enhancer = ImageEnhance.Contrast(self.original_pixmap)
            else:
                self.original_pixmap = self.current_pixmap
                enhancer = ImageEnhance.Contrast(self.original_pixmap)

            scale_factor = value / 50.0 if value != 50 else 1.0
            enhanced_image = enhancer.enhance(scale_factor)
            self.update_image(enhanced_image)
            self.current_pixmap = enhanced_image  
            self.current_contrast = value  

    def on_brightness_value_changed(self, value):
        self.brightness_dialog.input_field.setText(str(value)) 
        if self.current_pixmap is not None:
            if hasattr(self, 'original_pixmap'):
                enhancer = ImageEnhance.Brightness(self.original_pixmap)
            else:
                self.original_pixmap = self.current_pixmap
                enhancer = ImageEnhance.Brightness(self.original_pixmap)

            scale_factor = value / 50.0 if value != 50 else 1.0
            enhanced_image = enhancer.enhance(scale_factor)
            self.update_image(enhanced_image)
            self.current_pixmap = enhanced_image  
            self.current_brightness = value  

    def on_saturation_value_changed(self, value):
        self.saturation_dialog.input_field.setText(str(value))  
        if self.current_pixmap is not None:
            if hasattr(self, 'original_pixmap'):
                enhancer = ImageEnhance.Color(self.original_pixmap)
            else:
                self.original_pixmap = self.current_pixmap
                enhancer = ImageEnhance.Color(self.original_pixmap)

            scale_factor = value / 50.0 if value != 50 else 1.0
            enhanced_image = enhancer.enhance(scale_factor)
            self.update_image(enhanced_image)
            self.current_pixmap = enhanced_image  
            self.current_saturation = value  

    def import_image(self):
        image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if image_path:
            self.original_image = Image.open(image_path)  # Store the original image here
            self.current_pixmap = self.original_image  # Use original image for current_pixmap
            pixmap = QPixmap(image_path)
            self.graphics_scene.clear()
            
            self.resizable_item = ResizablePixmapItem(pixmap)
            self.graphics_scene.addItem(self.resizable_item)

            self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)

            # Reset enhancement values to defaults
            self.current_contrast = 50
            self.current_brightness = 50
            self.current_saturation = 50

            self.export_jpg_action.setEnabled(True)
            self.export_png_action.setEnabled(True)

            # Update sliders if dialogs are open
            if hasattr(self, 'contrast_dialog'):
                self.contrast_dialog.slider.setValue(self.current_contrast)
            if hasattr(self, 'brightness_dialog'):
                self.brightness_dialog.slider.setValue(self.current_brightness)
            if hasattr(self, 'saturation_dialog'):
                self.saturation_dialog.slider.setValue(self.current_saturation)

    def update_image(self, pil_image):
        q_image = ImageQt(pil_image)
        
        self.resizable_item = ResizablePixmapItem(QPixmap.fromImage(q_image))
        self.graphics_scene.addItem(self.resizable_item)
        self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def export_image(self, format):
        file_dialog = QFileDialog(self, "Save Image as {}".format(format.upper()))
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("Image Files (*.{})".format(format))
        file_dialog.setModal(True)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        
        if file_dialog.exec() == QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                if not file_path.lower().endswith(f".{format}"):
                    file_path += f".{format}"
                print(f"[DEBUG] Attempting to save image to: {file_path}")

                if hasattr(self, 'resizable_item'):
                    print(f"[DEBUG] Item in graphics scene: {type(self.resizable_item)}")
                    if isinstance(self.resizable_item, ResizablePixmapItem):
                        pixmap_to_save = self.resizable_item.current_pixmap
                        if pixmap_to_save and not pixmap_to_save.isNull():
                            print("[DEBUG] Pixmap is valid.")
                            success = pixmap_to_save.save(file_path, format.upper())
                            if success:
                                print(f"[SUCCESS] Image saved to {file_path}")
                            else:
                                print(f"[ERROR] Failed to save image to {file_path}. Check format or permissions.")
                        else:
                            print("[ERROR] Pixmap is null or invalid. Unable to save.")
                    else:
                        print("[ERROR] The item is not a ResizablePixmapItem.")
                else:
                    print("[ERROR] No resizable item found to export.")
            else:
                print("[ERROR] No file path selected.")
        else:
            print("[INFO] File dialog was cancelled.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEditor()
    window.show()
    sys.exit(app.exec())
