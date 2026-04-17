"""
主窗口（纯 UI 层）
所有业务逻辑由 AppController 处理。
"""

import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox,
    QStatusBar, QSplitter, QFrame, QToolBar,
    QTextEdit
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QTextCursor

# 自定义组件
from ui.widgets.image_viewer import CompareView
from ui.widgets.param_panel import ParamPanel
from ui.widgets.metrics_panel import MetricsPanel
from ui.widgets.history_panel import HistoryPanel

# 控制器
from ui.app_controller import AppController


class MainWindow(QMainWindow):
    """应用程序主窗口 — 纯 UI 层"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像去雾算法及应用研究")
        self.setMinimumSize(1100, 680)
        self.resize(1400, 800)

        # 创建控制器
        self._controller = AppController(self)

        # 构建 UI
        self._init_ui()
        self._init_toolbar()
        self._init_statusbar()

        # 连接控制器信号
        self._connect_controller()

    # ================================================================
    #  生命周期
    # ================================================================

    def closeEvent(self, event):
        self._controller.shutdown()
        event.accept()

    # ================================================================
    #  UI 初始化
    # ================================================================

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # 上下分割
        splitter_v = QSplitter(Qt.Vertical)

        # ── 上半部分 ──
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(4)

        # 图像对比视图
        self.compare_view = CompareView()
        self.compare_view.file_dropped.connect(self._on_file_dropped)
        top_layout.addWidget(self.compare_view, stretch=3)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_panel.setFixedWidth(360)

        # 参数面板（直接嵌入，不使用 ScrollArea）
        self._param_panel = ParamPanel()
        self._param_panel.apply_requested.connect(self._on_apply_requested)
        self._param_panel.reset_requested.connect(self._on_reset_requested)
        right_layout.addWidget(self._param_panel, stretch=5)

        # 质量指标面板（常显）
        self._metrics_panel = MetricsPanel()
        right_layout.addWidget(self._metrics_panel)

        top_layout.addWidget(right_panel)
        splitter_v.addWidget(top_widget)

        # ── 下半部分：日志(70%) + 历史(30%) 同行 ──
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(4)

        bottom_splitter = QSplitter(Qt.Horizontal)

        # 左侧: 处理日志
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(2)

        log_title = self._create_section_title("处理日志")
        log_layout.addWidget(log_title)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                color: #bbb;
                font-family: "Consolas", "Microsoft YaHei", monospace;
                font-size: 12px;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        log_layout.addWidget(self._log_text)

        bottom_splitter.addWidget(log_container)

        # 右侧: 操作历史
        self._history_panel = HistoryPanel()
        self._history_panel.undo_requested.connect(self._on_undo)
        bottom_splitter.addWidget(self._history_panel)

        # 设置分割比例 70:30
        bottom_splitter.setStretchFactor(0, 7)
        bottom_splitter.setStretchFactor(1, 3)

        bottom_layout.addWidget(bottom_splitter)
        splitter_v.addWidget(bottom_widget)

        # 上下分割比例 5:1
        splitter_v.setStretchFactor(0, 5)
        splitter_v.setStretchFactor(1, 1)

        main_layout.addWidget(splitter_v)

    def _init_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("打开", self)
        open_action.setToolTip("打开图像 (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_image)
        toolbar.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.setToolTip("保存结果 (Ctrl+S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_result)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        reset_action = QAction("重置", self)
        reset_action.setToolTip("重置为原图 (Ctrl+R)")
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._on_reset)
        toolbar.addAction(reset_action)

    def _init_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪 - 请打开图像文件 (Ctrl+O) 或拖拽图像到窗口")

    # ================================================================
    #  控制器信号连接
    # ================================================================

    def _connect_controller(self):
        ctrl = self._controller

        # 设置参数收集回调
        ctrl.set_collect_params_callback(self._param_panel.get_current_params)
        ctrl.set_current_algo_id_fn(self._param_panel.current_algo_id)

        # 控制器 → UI
        ctrl.display_updated.connect(self._on_display_updated)
        ctrl.metrics_updated.connect(self._on_metrics_updated)
        ctrl.evaluation_updated.connect(self._on_evaluation_updated)
        ctrl.status_message.connect(self._statusbar.showMessage)
        ctrl.log_message.connect(self._on_log_message)

    # ================================================================
    #  UI 事件 → 控制器
    # ================================================================

    def _on_file_dropped(self, file_path: str):
        self._controller.load_image(file_path)
        self._history_panel.clear()

    @Slot()
    def _on_open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开图像", "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*)"
        )
        if file_path:
            self._controller.load_image(file_path)
            self._history_panel.clear()

    @Slot()
    def _on_save_result(self):
        if not self._controller.has_result():
            QMessageBox.warning(self, "提示", "暂无处理结果可保存")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;TIFF (*.tiff)"
        )
        if file_path:
            self._controller.save_result(file_path)

    @Slot()
    def _on_reset(self):
        self._controller.reset_to_original()

    @Slot()
    def _on_undo(self):
        self._controller.undo()
        self._history_panel.remove_last()

    @Slot(str)
    def _on_apply_requested(self, algo_id: str):
        """用户点击"应用"按钮 → 触发处理"""
        self._controller.apply_processing()
        self._history_panel.add_entry(f"处理 ({algo_id})")

    @Slot(str)
    def _on_reset_requested(self, algo_id: str):
        """用户点击"重置参数"按钮"""
        self._controller.reset_preview(algo_id)
        self._metrics_panel.clear_metrics()

    # ================================================================
    #  控制器 → UI 更新
    # ================================================================

    @Slot(object, object)
    def _on_display_updated(self, current_image, result_image):
        if current_image is not None:
            self.compare_view.set_original(current_image)
        if result_image is not None:
            self.compare_view.set_result(result_image)
        else:
            self.compare_view.set_result(None)

    @Slot(dict)
    def _on_metrics_updated(self, metrics: dict):
        self._metrics_panel.update_metrics(
            psnr=metrics.get("psnr"),
            ssim=metrics.get("ssim"),
            mse=metrics.get("mse"),
            elapsed_ms=metrics.get("elapsed_ms")
        )

    @Slot(dict)
    def _on_evaluation_updated(self, evaluation: dict):
        self._metrics_panel.update_metrics(evaluation=evaluation)

    @Slot(str, str)
    def _on_log_message(self, msg: str, level: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#8ab4f8",
            "OK":   "#4CAF50",
            "WARN": "#ff9800",
            "ERR":  "#f44336",
            "PROC": "#ffeb3b",
        }
        color = color_map.get(level, "#bbb")
        self._log_text.append(
            f'<span style="color:#666">[{ts}]</span> '
            f'<span style="color:{color}">{msg}</span>'
        )
        cursor = self._log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._log_text.setTextCursor(cursor)

    # ================================================================
    #  辅助方法
    # ================================================================

    @staticmethod
    def _create_section_title(text: str):
        """创建区域标题标签"""
        from PySide6.QtWidgets import QLabel
        label = QLabel(text)
        label.setStyleSheet("color: #8ab4f8; font-weight: bold; font-size: 13px;")
        return label
