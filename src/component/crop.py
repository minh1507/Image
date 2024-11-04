import sys
from PySide6.QtWidgets import (QGraphicsItem, 
                               QGraphicsRectItem)  
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt, QRectF, QPointF

class CropItem(QGraphicsRectItem):
    def __init__(self):
        super().__init__()
        self.setPen(QPen(Qt.red, 2, Qt.DashLine))
        self.setBrush(QColor(255, 0, 0, 50)) 
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self.resizing = False
        self.resize_handle = QGraphicsRectItem(self)
        self.resize_handle.setRect(QRectF(-5, -5, 10, 10))  # Resize handle size
        self.resize_handle.setBrush(Qt.darkGray)
        self.resize_handle.setPen(Qt.NoPen)
        self.resize_handle.setCursor(Qt.SizeFDiagCursor)
        self.update_resize_handle_position()

    def update_resize_handle_position(self):
        """Update the position of the resize handle."""
        rect = self.rect()
        self.resize_handle.setPos(rect.bottomRight() - QPointF(5, 5)) 

    def mousePressEvent(self, event):
        """Handle mouse press events for resizing or moving."""
        if self.resize_handle.isUnderMouse():
            self.resizing = True
            self.resize_start_pos = event.pos()
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for resizing or moving."""
        if self.resizing:
            self.resize(event.pos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset resizing flag and cursor."""
        if self.resizing:
            self.resizing = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def resize(self, pos):
        """Resize the crop rectangle based on the mouse position."""
        rect = self.rect()
        new_rect = QRectF(rect.topLeft(), pos)
        # Ensure a minimum size for the crop rectangle
        if new_rect.width() > 10 and new_rect.height() > 10:
            self.setRect(new_rect.normalized())
            self.update_resize_handle_position()
