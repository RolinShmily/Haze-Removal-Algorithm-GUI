"""
深色主题样式表
"""

STYLESHEET = """
/* ===== 全局 ===== */
QMainWindow {
    background-color: #2b2b2b;
}
QWidget {
    color: #ddd;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QLabel {
    background: transparent;
}

/* ===== 工具栏 ===== */
QToolBar {
    background: #333;
    border-bottom: 1px solid #444;
    spacing: 6px;
    padding: 2px 4px;
}
QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    color: #ccc;
}
QToolBar QToolButton:hover {
    background: #3a6ea5;
    border-color: #3a6ea5;
    color: white;
}
QToolBar QToolButton:pressed {
    background: #2a5e95;
}
QToolBar::separator {
    width: 1px;
    background: #555;
    margin: 4px 2px;
}

/* ===== 菜单 ===== */
QMenuBar {
    background: #333;
    border-bottom: 1px solid #444;
}
QMenuBar::item {
    padding: 4px 10px;
}
QMenuBar::item:selected {
    background: #3a6ea5;
    border-radius: 3px;
}
QMenu {
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 2px;
}
QMenu::item {
    padding: 4px 24px;
    border-radius: 2px;
}
QMenu::item:selected {
    background: #3a6ea5;
}

/* ===== GroupBox ===== */
QGroupBox {
    border: 1px solid #444;
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: #ccc;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #8ab4f8;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #3a6ea5;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    color: white;
    font-weight: bold;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #4a8ed5;
}
QPushButton:pressed {
    background-color: #2a5e95;
}
QPushButton:disabled {
    background-color: #444;
    color: #666;
}
QPushButton#resetBtn {
    background-color: #555;
}
QPushButton#resetBtn:hover {
    background-color: #666;
}

/* ===== 滑块 ===== */
QSlider::groove:horizontal {
    height: 6px;
    background: #444;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #3a6ea5;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #5aaef5;
    width: 18px;
    height: 18px;
    margin: -6px 0;
}
QSlider::sub-page:horizontal {
    background: #3a6ea5;
    border-radius: 3px;
}

/* ===== Tab ===== */
QTabWidget::pane {
    border: 1px solid #444;
    border-radius: 4px;
    background: #2b2b2b;
}
QTabBar::tab {
    background: #333;
    border: 1px solid #444;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #aaa;
}
QTabBar::tab:selected {
    background: #3a6ea5;
    color: white;
}
QTabBar::tab:hover:!selected {
    background: #3a3a3a;
    color: #ddd;
}

/* ===== ComboBox ===== */
QComboBox {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #3a6ea5;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #aaa;
}
QComboBox QAbstractItemView {
    background: #3a3a3a;
    border: 1px solid #555;
    selection-background-color: #3a6ea5;
    outline: none;
}

/* ===== CheckBox ===== */
QCheckBox {
    spacing: 6px;
    color: #ccc;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #666;
    border-radius: 3px;
    background: #3a3a3a;
}
QCheckBox::indicator:checked {
    background: #3a6ea5;
    border-color: #3a6ea5;
}

/* ===== ScrollArea ===== */
QScrollArea {
    background: #2b2b2b;
    border: none;
}
QScrollBar:vertical {
    background: #2b2b2b;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #555;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ===== 状态栏 ===== */
QStatusBar {
    background: #252525;
    color: #888;
    border-top: 1px solid #333;
    font-size: 12px;
}

/* ===== Splitter ===== */
QSplitter::handle {
    background: #444;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QSplitter::handle:hover {
    background: #3a6ea5;
}

/* ===== ProgressBar ===== */
QProgressBar {
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
    color: #aaa;
    font-size: 11px;
}
QProgressBar::chunk {
    background: #3a6ea5;
    border-radius: 3px;
}

/* ===== SpinBox ===== */
QSpinBox, QDoubleSpinBox {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 2px 6px;
    color: #ddd;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3a6ea5;
}

/* ===== ListWidget (操作历史) ===== */
QListWidget {
    background: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    font-size: 12px;
}
QListWidget::item {
    padding: 2px 4px;
    border-bottom: 1px solid #333;
}
QListWidget::item:selected {
    background: #3a6ea5;
}
"""
