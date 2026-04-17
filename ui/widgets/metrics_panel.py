"""
质量评估指标展示面板

展示去雾算法处理的客观质量指标:
    PSNR / SSIM / MSE / 耗时 / 对比度σ / 色调还原d / 有效细节I / 结构信息S / 综合q

"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt


class MetricsPanel(QWidget):
    """质量指标展示面板 — 常显，两列紧凑布局"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # 标题
        title = QLabel("质量评估")
        title.setStyleSheet("color: #8ab4f8; font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # 两列指标网格
        grid = QGridLayout()
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)

        # 左列
        self._psnr_label  = self._add_metric_cell(grid, 0, 0, "PSNR", "-- dB")
        self._ssim_label  = self._add_metric_cell(grid, 1, 0, "SSIM", "--")
        self._mse_label   = self._add_metric_cell(grid, 2, 0, "MSE", "--")
        self._time_label  = self._add_metric_cell(grid, 3, 0, "耗时", "-- ms")
        self._sigma_label = self._add_metric_cell(grid, 4, 0, "对比度 σ", "--")

        # 右列
        self._d_label     = self._add_metric_cell(grid, 0, 1, "色调还原 d", "--")
        self._ivalid_label= self._add_metric_cell(grid, 1, 1, "有效细节 I", "--")
        self._s_label     = self._add_metric_cell(grid, 2, 1, "结构信息 S", "--")
        self._q_label     = self._add_metric_cell(grid, 3, 1, "综合指标 q", "--")

        layout.addLayout(grid)

    def _add_metric_cell(self, grid: QGridLayout, row: int, col: int,
                         name: str, default: str) -> QLabel:
        """在网格中添加一个指标格"""
        cell = QFrame()
        cell.setStyleSheet("""
            QFrame {
                background: #252525;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 1px 4px;
            }
        """)
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(2, 1, 2, 1)
        cell_layout.setSpacing(0)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: #888; font-size: 10px;")

        val_lbl = QLabel(default)
        val_lbl.setStyleSheet("color: #8ab4f8; font-size: 11px; font-weight: bold;")
        val_lbl.setAlignment(Qt.AlignCenter)

        cell_layout.addWidget(name_lbl)
        cell_layout.addWidget(val_lbl)

        grid.addWidget(cell, row, col)
        return val_lbl

    def update_metrics(
        self,
        psnr: float = None,
        ssim: float = None,
        mse: float = None,
        elapsed_ms: float = None,
        evaluation: dict = None
    ):
        """更新指标显示"""
        if psnr is not None:
            if psnr == float('inf'):
                self._psnr_label.setText("inf")
            else:
                self._psnr_label.setText(f"{psnr:.2f}")

        if ssim is not None:
            self._ssim_label.setText(f"{ssim:.4f}")

        if mse is not None:
            self._mse_label.setText(f"{mse:.2f}")

        if elapsed_ms is not None:
            self._time_label.setText(f"{elapsed_ms:.0f}ms")

        if evaluation is not None:
            self._sigma_label.setText(f"{evaluation.get('sigma', '--')}")
            self._d_label.setText(f"{evaluation.get('d', '--')}")
            self._ivalid_label.setText(f"{evaluation.get('I_valid', '--')}")
            self._s_label.setText(f"{evaluation.get('S', '--')}")
            self._q_label.setText(f"{evaluation.get('q', '--')}")

    def clear_metrics(self):
        """清空所有指标显示"""
        self._psnr_label.setText("--")
        self._ssim_label.setText("--")
        self._mse_label.setText("--")
        self._time_label.setText("--")
        self._sigma_label.setText("--")
        self._d_label.setText("--")
        self._ivalid_label.setText("--")
        self._s_label.setText("--")
        self._q_label.setText("--")
