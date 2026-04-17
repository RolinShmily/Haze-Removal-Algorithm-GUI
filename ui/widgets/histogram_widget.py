"""
直方图显示组件
用于显示灰度直方图或 BGR 三通道直方图
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush


class HistogramWidget(QWidget):
    """直方图绘制组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hist_data = None
        self._is_bgr = False
        self._bgr_hists = None
        self.setMinimumSize(256, 120)
        self.setMaximumHeight(160)

    def set_histogram_gray(self, hist):
        self._hist_data = hist
        self._is_bgr = False
        self._bgr_hists = None
        self.update()

    def set_histogram_bgr(self, b_hist, g_hist, r_hist):
        self._bgr_hists = (b_hist, g_hist, r_hist)
        self._is_bgr = True
        self._hist_data = None
        self.update()

    def clear(self):
        self._hist_data = None
        self._bgr_hists = None
        self._is_bgr = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))

        if self._is_bgr and self._bgr_hists:
            self._draw_bgr_histogram(painter, w, h)
        elif self._hist_data is not None:
            self._draw_gray_histogram(painter, w, h)
        else:
            painter.setPen(QPen(QColor(120, 120, 120)))
            painter.drawText(self.rect(), Qt.AlignCenter, "直方图")
        painter.end()

    def _draw_gray_histogram(self, painter, w, h):
        hist = self._hist_data
        if hist is None or len(hist) == 0:
            return
        max_val = max(hist.max(), 1)
        margin = 5
        draw_h = h - 2 * margin
        draw_w = w - 2 * margin
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        bar_w = draw_w / 256.0
        for i in range(256):
            bar_h = (hist[i] / max_val) * draw_h
            x = margin + i * bar_w
            y = h - margin - bar_h
            painter.drawRect(int(x), int(y), max(int(bar_w), 1), int(bar_h))

    def _draw_bgr_histogram(self, painter, w, h):
        b_hist, g_hist, r_hist = self._bgr_hists
        margin = 5
        draw_h = h - 2 * margin
        draw_w = w - 2 * margin
        bar_w = draw_w / 256.0
        max_val = max(b_hist.max(), g_hist.max(), r_hist.max(), 1)
        colors = [
            (QColor(255, 0, 0, 100), r_hist),
            (QColor(0, 255, 0, 100), g_hist),
            (QColor(0, 0, 255, 100), b_hist),
        ]
        for color, hist in colors:
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(QBrush(color))
            for i in range(256):
                bar_h = (hist[i] / max_val) * draw_h
                x = margin + i * bar_w
                y = h - margin - bar_h
                painter.drawRect(int(x), int(y), max(int(bar_w), 1), int(bar_h))


class HistogramPanel(QWidget):
    """直方图面板：原图直方图 + 结果直方图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        left = QVBoxLayout()
        label_src = QLabel("原图直方图")
        label_src.setAlignment(Qt.AlignCenter)
        label_src.setStyleSheet("color: #ccc; font-size: 12px;")
        self.hist_original = HistogramWidget()
        left.addWidget(label_src)
        left.addWidget(self.hist_original)
        layout.addLayout(left)

        right = QVBoxLayout()
        label_dst = QLabel("结果直方图")
        label_dst.setAlignment(Qt.AlignCenter)
        label_dst.setStyleSheet("color: #ccc; font-size: 12px;")
        self.hist_result = HistogramWidget()
        right.addWidget(label_dst)
        right.addWidget(self.hist_result)
        layout.addLayout(right)
