import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QMenu, QFileDialog, 
                               QPushButton, QGraphicsView, 
                               QGraphicsScene, QSlider, QFrame, QToolTip, QGraphicsPixmapItem, QGraphicsItem)
from PySide6.QtGui import QAction, QPixmap, QIcon, QFont
from PySide6.QtCore import Qt, QSize, QRectF, QPointF


from PySide6.QtWidgets import QGraphicsRectItem


class ResizablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.original_pixmap = pixmap
        self.current_pixmap = pixmap  # Store the current resized pixmap
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.SizeAllCursor)

        self.is_resizing = False
        self.resize_start_pos = None
        self.current_handle = None

        self.resize_handle = QGraphicsRectItem(self)
        self.resize_handle.setRect(QRectF(-5, -5, 10, 10))
        self.resize_handle.setBrush(Qt.darkGray)
        self.resize_handle.setPen(Qt.NoPen)
        self.resize_handle.setCursor(Qt.SizeFDiagCursor)

        self.update_resize_handle_position()

    def update_resize_handle_position(self):
        rect = self.boundingRect()
        self.resize_handle.setPos(rect.bottomRight() - QPointF(5, 5))  # Adjust for the handle's size

    def mousePressEvent(self, event):
        if self.resize_handle.isUnderMouse():
            self.is_resizing = True
            self.current_handle = self.resize_handle
            self.resize_start_pos = event.pos()
            self.setCursor(Qt.SizeFDiagCursor)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing and self.current_handle:
            self.resize_image(event.pos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            self.setCursor(Qt.SizeAllCursor)
        else:
            super().mouseReleaseEvent(event)

    def resize_image(self, pos):
        rect = self.boundingRect()
        new_width = max(pos.x(), 10)
        new_height = max(pos.y(), 10)

        # Maintain aspect ratio
        aspect_ratio = self.original_pixmap.width() / self.original_pixmap.height()
        if new_width / new_height > aspect_ratio:
            new_width = new_height * aspect_ratio
        else:
            new_height = new_width / aspect_ratio

        # Resize the pixmap and store it
        resized_pixmap = self.original_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(resized_pixmap)
        self.current_pixmap = resized_pixmap  # Store the resized pixmap

        self.update_resize_handle_position()


class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photoshop-like App")
        self.setGeometry(100, 100, 1200, 800)
        
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

        contrast_label = QLabel("Adjust Contrast")
        contrast_label.setStyleSheet("color: white;")
        contrast_slider = QSlider(Qt.Horizontal)
        contrast_slider.setRange(-100, 100)
        
        grayscale_button = QPushButton("Convert to Grayscale")
        grayscale_button.setFixedHeight(40)

        right_sidebar.addWidget(contrast_label)
        right_sidebar.addWidget(contrast_slider)
        right_sidebar.addWidget(grayscale_button)

        frame = QFrame()
        frame.setLayout(right_sidebar)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFixedWidth(200)  

        layout.addWidget(frame)

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        
        import_action = QAction("Import", self)
        import_action.triggered.connect(self.import_image)
        file_menu.addAction(import_action)

        export_menu = QMenu("Export", self)
        
        export_jpg_action = QAction("JPG", self)
        export_jpg_action.triggered.connect(lambda: self.export_image("jpg"))
        export_menu.addAction(export_jpg_action)

        export_png_action = QAction("PNG", self)
        export_png_action.triggered.connect(lambda: self.export_image("png"))
        export_menu.addAction(export_png_action)

        file_menu.addMenu(export_menu)

        settings_menu = menubar.addMenu("Settings")
    

    def import_image(self):
        image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if image_path:
            pixmap = QPixmap(image_path)
            self.graphics_scene.clear()
            resizable_item = ResizablePixmapItem(pixmap)
            self.graphics_scene.addItem(resizable_item)
            self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def export_image(self, format):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image as {}".format(format.upper()), "", "Image Files (*.{})".format(format))
        if file_path:
            if self.graphics_scene.items():
                resizable_item = self.graphics_scene.items()[0]  
                if isinstance(resizable_item, ResizablePixmapItem):
                    pixmap_to_save = resizable_item.current_pixmap
                    if pixmap_to_save.save(file_path, format.upper()):
                        print(f"Image saved successfully to {file_path}")
                    else:
                        print(f"Failed to save image to {file_path}")
            else:
                print("No image found to export.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEditor()
    window.show()
    sys.exit(app.exec())
