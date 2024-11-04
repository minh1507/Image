import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QMenu, QFileDialog, 
                               QPushButton, QGraphicsView, 
                               QGraphicsScene, QFrame, QToolTip, 
                               QGraphicsPixmapItem, QDialog, QGridLayout,
                               QColorDialog, QFontDialog, QLineEdit, QLabel, QSlider,
                               QMessageBox)  
from PySide6.QtGui import QAction, QPixmap, QIcon, QFont, QTransform
from PySide6.QtCore import Qt, QSize, QRectF
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageQt
from PIL.ImageQt import ImageQt  
from component.crop import CropItem
from component.resize import ResizablePixmapItem
from component.adjust import AdjustDialog

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Redy")
        self.setGeometry(100, 100, 1200, 800)

        self.current_contrast = 50  
        self.current_brightness = 50 
        self.current_saturation = 50  
        self.current_sharpening = 50 
        self.current_blur = 0 
        self.last_click_pos = None
        self.rotation_angle = 0 
        self.current_pixmap = None 
        self.original_image = None  
        self.flipped_image = None  
        self.is_flipped = False  
        self.current_text_color = Qt.white  
        
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
            ("Sharpen", self.show_sharpen_popup),
            ("Blur", self.show_blur_popup),
            ("Add Text", self.show_add_text_dialog),
            ("Pick Color", self.activate_color_picker),
            ("Zoom In", self.zoom_in_image), 
            ("Zoom Out", self.zoom_out_image)
        ]

        for i, (feature_name, handler) in enumerate(features):
            button = QPushButton(feature_name)
            button.clicked.connect(handler)
            feature_grid.addWidget(button, i // 2, i % 2)

        right_sidebar.addLayout(feature_grid)
        right_sidebar.addStretch()
        layout.addLayout(right_sidebar)
    
    def zoom_in_image(self):
        if self.current_pixmap is not None:
            scale_factor = 1.2  
            self.graphics_view.scale(scale_factor, scale_factor)  
        
    def zoom_out_image(self):
        if self.current_pixmap is not None:
            scale_factor = 0.8  
            self.graphics_view.scale(scale_factor, scale_factor)  

    def activate_color_picker(self):
        self.graphics_view.setCursor(Qt.CrossCursor)  
        self.graphics_view.mousePressEvent = self.pick_color_from_image
    
    def pick_color_from_image(self, event):
        if self.current_pixmap is not None:
            pos = event.pos()
            scene_pos = self.graphics_view.mapToScene(pos)

            item = self.graphics_scene.itemAt(scene_pos, QTransform())
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap()
                x = int(scene_pos.x())
                y = int(scene_pos.y())
                if 0 <= x < pixmap.width() and 0 <= y < pixmap.height():
                    color = pixmap.toImage().pixelColor(x, y)
                    self.current_text_color = color  
                    self.graphics_view.setCursor(Qt.ArrowCursor) 
                    self.show_color_picked_message(color)

    def show_color_picked_message(self, color):
        rgb_value = f"RGB({color.red()}, {color.green()}, {color.blue()})"
        color_message = f"Color: {rgb_value}"

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Color Picked")
        message_box.setText(color_message)

        copy_button = message_box.addButton("Copy", QMessageBox.ActionRole)
        message_box.addButton(QMessageBox.Ok)

        message_box.exec()

        if message_box.clickedButton() == copy_button:
            clipboard = QApplication.clipboard()
            clipboard.setText(rgb_value)

    def show_add_text_dialog(self):
        text_dialog = QDialog(self)
        text_dialog.setWindowTitle("Add Text to Image")
        text_dialog.setGeometry(300, 300, 300, 150)
        layout = QVBoxLayout()

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text here...")
        layout.addWidget(self.text_input)

        add_text_button = QPushButton("Add Text")
        add_text_button.clicked.connect(lambda: self.add_text_to_image(self.text_input.text()))
        layout.addWidget(add_text_button)

        text_dialog.setLayout(layout)
        text_dialog.exec()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_text_color = color


    def choose_font(self):
        """Open a dialog for font selection."""
        font, ok = QFontDialog.getFont()  
        if ok:  
            self.selected_font = font  
            print(f"Selected font: {font.family()}, size: {font.pointSize()}")

    def add_text_to_image(self, text):
        if self.current_pixmap is not None:
            q_image = self.current_pixmap.toqimage()  
            pil_image = Image.frombytes("RGBA", (q_image.width(), q_image.height()), 
                                        q_image.bits(), "raw", "BGRA", 0, 1)

            draw = ImageDraw.Draw(pil_image)
            font = ImageFont.load_default()
            text_position = (10, 10)  
            text_color = (255, 255, 255)  
            draw.text(text_position, text, fill=text_color, font=font)

            self.update_image(pil_image)  

    def reset_image(self):
        """Reset the image to its original state."""
        if self.original_image is not None:
            self.update_image(self.original_image)  
            self.current_contrast = 50
            self.current_brightness = 50
            self.current_saturation = 50
            self.current_sharpening = 50 
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

    def show_blur_popup(self):
        """Show a dialog to adjust the blur."""
        self.blur_dialog = AdjustDialog("Adjust Blur", 0, 100, self.current_blur, self.on_blur_value_changed)
        self.blur_dialog.show()

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
        """Show the cropping dialog with the crop overlay item."""
        q_image = ImageQt(self.current_pixmap)  
        pixmap = QPixmap.fromImage(q_image)

        self.graphics_scene.clear()
        self.original_pixmap_item = QGraphicsPixmapItem(pixmap)
        self.graphics_scene.addItem(self.original_pixmap_item)

        self.crop_item = CropItem()
        self.graphics_scene.addItem(self.crop_item)
        self.crop_item.setRect(QRectF(50, 50, 100, 100))  
        self.crop_item.update_resize_handle_position()

        self.crop_widget = QWidget()
        crop_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        confirm_button = QPushButton("Confirm Crop")
        confirm_button.clicked.connect(self.confirm_crop)

        cancel_button = QPushButton("Cancel Crop")
        cancel_button.clicked.connect(self.cancel_crop)

        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        crop_layout.addLayout(button_layout)
        self.crop_widget.setLayout(crop_layout)

        self.graphics_scene.addWidget(self.crop_widget)
        self.crop_widget.show()

        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)

    def get_crop_rectangle(self):
        if self.crop_item:
            rect = self.crop_item.rect()
            return (rect.x(), rect.y(), rect.width(), rect.height())
        return None

    def confirm_crop(self):
        """Confirm cropping, update the image, and remove the crop overlay."""
        if self.crop_item is not None:
            try:
                crop_rect = self.get_crop_rectangle() 

                if crop_rect:
                    x, y, width, height = crop_rect
                    pil_image = self.original_image.crop((x, y, x + width, y + height))

                    self.current_pixmap = pil_image
                    self.update_image(self.current_pixmap)  

                    if self.crop_item.scene() is not None:  
                        self.graphics_scene.removeItem(self.crop_item)
                        print("Crop item removed from the scene.")
                    else:
                        print("Crop item is already deleted or not in the scene.")

                else:
                    print("Invalid crop rectangle.")

                self.crop_item = None

            except RuntimeError as e:
                print(f"Runtime error during confirm crop: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
        else:
            print("No crop item to confirm.")

    def cancel_crop(self):
        """Cancel cropping and remove crop overlay and buttons."""
        if self.crop_item is not None:
            try:
                self.graphics_scene.removeItem(self.crop_item)
                print("Crop item removed from the scene.")
            
                self.crop_item = None  

            except RuntimeError as e:
                print(f"Runtime error during cancel crop: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

        if hasattr(self, 'crop_widget') and self.crop_widget is not None:
            self.crop_widget.hide()
            self.crop_widget = None 

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

    def on_blur_value_changed(self, value):
        self.blur_dialog.input_field.setText(str(value))

        if self.current_pixmap is not None:
            if hasattr(self, 'original_pixmap'):
                pil_image = self.original_pixmap
            else:
                self.original_pixmap = self.current_pixmap
                pil_image = self.original_pixmap

            q_image = pil_image.toqimage()
            pil_image = Image.frombytes("RGBA", (q_image.width(), q_image.height()),
                                        q_image.bits(), "raw", "BGRA", 0, 1)

            blur_radius = value / 20.0  
            blurred_image = pil_image.filter(ImageFilter.GaussianBlur(blur_radius))  

            self.update_image(blurred_image)  
            self.current_pixmap = blurred_image  
            self.current_blur = value  
            
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
            self.original_image = Image.open(image_path)  
            self.current_pixmap = self.original_image  
            pixmap = QPixmap(image_path)
            self.graphics_scene.clear()
            
            self.resizable_item = ResizablePixmapItem(pixmap)
            self.graphics_scene.addItem(self.resizable_item)

            self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)

            self.current_contrast = 50
            self.current_brightness = 50
            self.current_saturation = 50

            self.export_jpg_action.setEnabled(True)
            self.export_png_action.setEnabled(True)

            if hasattr(self, 'contrast_dialog'):
                self.contrast_dialog.slider.setValue(self.current_contrast)
            if hasattr(self, 'brightness_dialog'):
                self.brightness_dialog.slider.setValue(self.current_brightness)
            if hasattr(self, 'saturation_dialog'):
                self.saturation_dialog.slider.setValue(self.current_saturation)

    def update_image(self, pil_image):
        """Updates the display with the new PIL image."""
        
        q_image = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(q_image)
        
        self.graphics_scene.clear() 
        
        self.resizable_item = ResizablePixmapItem(pixmap)
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
