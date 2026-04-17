"""
图像显示组件
支持图像的缩放显示、拖拽上传、双图对比
"""

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from core.utils import numpy_to_qpixmap


class ImageLabel(QLabel):
    """可缩放显示图像的标签，支持拖拽文件"""

    file_dropped = Signal(str)

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._pixmap = QPixmap()
        self._is_empty = True
        self.setMinimumSize(200, 150)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self._update_empty_style()

    def _update_empty_style(self):
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 2px dashed #555;
                border-radius: 8px;
                color: #666;
                font-size: 14px;
            }
        """)
        self.setText(f"[ {self._title} ]")

    def _update_filled_style(self):
        self.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)

    def set_image(self, image):
        if image is None:
            self._pixmap = QPixmap()
            self._is_empty = True
            self._update_empty_style()
            return

        self._is_empty = False
        self._pixmap = numpy_to_qpixmap(image)
        self._update_filled_style()
        self._update_scaled()

    def _update_scaled(self):
        if self._pixmap.isNull():
            return
        scaled = self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._pixmap.isNull():
            self._update_scaled()

    # ── 拖拽事件 ──

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_image_url(urls[0]):
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QLabel {
                        background-color: #1a2a1a;
                        border: 2px dashed #4CAF50;
                        border-radius: 8px;
                        color: #4CAF50;
                        font-size: 14px;
                    }
                """)

    def dragLeaveEvent(self, event):
        if self._is_empty:
            self._update_empty_style()
        else:
            self._update_filled_style()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if self._is_image_url(urls[0]):
                self.file_dropped.emit(path)
        if self._is_empty:
            self._update_empty_style()
        else:
            self._update_filled_style()

    @staticmethod
    def _is_image_url(url: QUrl) -> bool:
        if not url.isLocalFile():
            return False
        ext = url.toLocalFile().lower()
        return any(ext.endswith(e) for e in
                   ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'])


class CompareView(QWidget):
    """双图对比视图：原图 + 结果"""

    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.label_original = ImageLabel("原图")
        self.label_result = ImageLabel("结果")

        # 中间分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("color: #555;")

        layout.addWidget(self.label_original, stretch=1)
        layout.addWidget(separator)
        layout.addWidget(self.label_result, stretch=1)

        # 转发拖拽信号
        self.label_original.file_dropped.connect(self.file_dropped.emit)
        self.label_result.file_dropped.connect(self.file_dropped.emit)

    def set_original(self, image):
        self.label_original.set_image(image)

    def set_result(self, image):
        self.label_result.set_image(image)

    def clear_all(self):
        self.label_original.set_image(None)
        self.label_result.set_image(None)
