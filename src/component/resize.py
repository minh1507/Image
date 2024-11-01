import sys
import os
from PySide6.QtWidgets import (
                               QMenu,
                               QGraphicsPixmapItem, QGraphicsItem, 
                               QGraphicsRectItem)  
from PySide6.QtCore import Qt, QRectF, QPointF

class ResizablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.original_pixmap = pixmap
        self.current_pixmap = pixmap  
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

    def contextMenuEvent(self, event):
        context_menu = QMenu()
        remove_action = context_menu.addAction("Remove Image")
        action = context_menu.exec(event.screenPos())
        if action == remove_action:
            self.remove_image()

    def remove_image(self):
        if self.scene():
            self.scene().removeItem(self)
            del self  

    def update_resize_handle_position(self):
        rect = self.boundingRect()
        self.resize_handle.setPos(rect.bottomRight() - QPointF(5, 5)) 

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

        aspect_ratio = self.original_pixmap.width() / self.original_pixmap.height()
        if new_width / new_height > aspect_ratio:
            new_width = new_height * aspect_ratio
        else:
            new_height = new_width / aspect_ratio

        resized_pixmap = self.original_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(resized_pixmap)
        self.current_pixmap = resized_pixmap  

        self.update_resize_handle_position()
