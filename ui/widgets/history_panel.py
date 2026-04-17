"""
操作历史面板
- 撤销按钮与标题同行
- 历史条目使用两列展示，带时间戳
"""

import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QFrame
)
from PySide6.QtCore import Signal, Qt


class HistoryPanel(QWidget):
    """操作历史面板 — 标题+撤销同行，两列时间戳历史"""

    undo_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(3)

        # ── 标题行: "操作历史" + 撤销按钮 ──
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title = QLabel("操作历史")
        title.setStyleSheet("color: #8ab4f8; font-weight: bold; font-size: 12px;")
        title_row.addWidget(title)

        title_row.addStretch()

        self.undo_btn = QPushButton("撤销")
        self.undo_btn.setObjectName("resetBtn")
        self.undo_btn.setFixedHeight(22)
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_requested.emit)
        title_row.addWidget(self.undo_btn)

        layout.addLayout(title_row)

        # ── 历史列表 ──
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 3px;
                font-size: 11px;
                padding: 2px;
            }
            QListWidget::item {
                padding: 1px 4px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background: #3a6ea5;
            }
        """)
        layout.addWidget(self.history_list)

    def add_entry(self, description: str):
        """添加历史记录（带时间戳）"""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.history_list.addItem(f"[{ts}] {description}")
        self.history_list.scrollToBottom()
        self.undo_btn.setEnabled(True)

    def remove_last(self):
        """移除最后一条记录"""
        if self.history_list.count() > 0:
            self.history_list.takeItem(self.history_list.count() - 1)
        self.undo_btn.setEnabled(self.history_list.count() > 0)

    def clear(self):
        """清空历史"""
        self.history_list.clear()
        self.undo_btn.setEnabled(False)
