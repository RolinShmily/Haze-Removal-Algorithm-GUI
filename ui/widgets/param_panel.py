"""
参数面板组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSlider,
    QButtonGroup, QFrame
)
from PySide6.QtCore import Qt, Signal

from core.registry import AlgorithmRegistry, ParamDef


# 按钮样式
_PILL_STYLE_SELECTED = """
    QPushButton {
        background-color: #3a6ea5;
        color: white;
        border: 2px solid #5aaef5;
        border-radius: 12px;
        padding: 3px 6px;
        font-size: 11px;
        font-weight: bold;
        min-height: 18px;
    }
"""

_PILL_STYLE_UNSELECTED = """
    QPushButton {
        background-color: #333;
        color: #aaa;
        border: 2px solid #555;
        border-radius: 12px;
        padding: 3px 6px;
        font-size: 11px;
        min-height: 18px;
    }
    QPushButton:hover {
        background-color: #444;
        color: #ccc;
        border-color: #666;
    }
"""


class ParamSlider(QWidget):
    """紧凑型参数滑块"""

    def __init__(self, param_def: ParamDef, parent=None):
        super().__init__(parent)
        self._param = param_def
        self._decimals = param_def.decimals
        self._scale = 10 ** param_def.decimals
        self._odd_only = param_def.odd_only

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)

        # 参数标签
        self._name_label = QLabel(param_def.label)
        self._name_label.setFixedWidth(58)
        self._name_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self._name_label)

        # 滑块
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(int(param_def.min_val * self._scale))
        self._slider.setMaximum(int(param_def.max_val * self._scale))
        self._slider.setValue(int(param_def.default * self._scale))
        self._slider.setSingleStep(int(param_def.step * self._scale))
        layout.addWidget(self._slider, stretch=1)

        # 值显示
        self._value_label = QLabel(self._format(param_def.default))
        self._value_label.setFixedWidth(40)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value_label.setStyleSheet("color: #8ab4f8; font-size: 11px;")
        layout.addWidget(self._value_label)

        self._slider.valueChanged.connect(self._on_value_changed)

    def _format(self, val: float) -> str:
        return f"{val:.{self._decimals}f}"

    def _on_value_changed(self, raw_val: int):
        val = raw_val / self._scale
        if self._odd_only:
            int_val = int(val)
            if int_val % 2 == 0:
                int_val += 1
                val = float(int_val)
                self._slider.blockSignals(True)
                self._slider.setValue(int(val * self._scale))
                self._slider.blockSignals(False)
        self._value_label.setText(self._format(val))

    def value(self) -> float:
        val = self._slider.value() / self._scale
        if self._odd_only:
            int_val = int(val)
            if int_val % 2 == 0:
                int_val += 1
            return float(int_val)
        return val

    def set_value(self, val: float):
        self._slider.setValue(int(val * self._scale))


class ParamPanel(QWidget):
    apply_requested = Signal(str)
    reset_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._params = {}
        self._combos = {}
        self._descriptors = {}
        self._current_algo_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # ── 算法选择按钮区: 3×2 网格 ──
        algo_grid = QGridLayout()
        algo_grid.setSpacing(4)
        algo_grid.setContentsMargins(0, 0, 0, 0)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        algos = AlgorithmRegistry.all_algorithms()
        for idx, desc in enumerate(algos):
            btn = QPushButton(desc.name)
            btn.setCheckable(True)
            btn.setStyleSheet(_PILL_STYLE_UNSELECTED)
            row, col = divmod(idx, 3)
            algo_grid.addWidget(btn, row, col)
            self._btn_group.addButton(btn, id=idx)
            self._descriptors[desc.id] = desc

        layout.addLayout(algo_grid)

        # ── 分隔线 ──
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #444; max-height: 1px;")
        layout.addWidget(sep1)

        # ── 参数容器 ──
        self._param_container = QVBoxLayout()
        self._param_container.setSpacing(2)
        layout.addLayout(self._param_container)

        # ── 分隔线 ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #444; max-height: 1px;")
        layout.addWidget(sep2)

        # ── 操作按钮: 纵向排布 ──
        self._apply_btn = QPushButton("应用")
        self._apply_btn.clicked.connect(self._on_apply)
        layout.addWidget(self._apply_btn)

        self._reset_btn = QPushButton("重置参数")
        self._reset_btn.setObjectName("resetBtn")
        self._reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(self._reset_btn)

        # 按钮组信号
        self._btn_group.idClicked.connect(self._on_algo_clicked)

        # 默认选中第一个算法
        if algos:
            self._current_algo_id = algos[0].id
            self._build_params(algos[0])
            first_btn = self._btn_group.button(0)
            if first_btn:
                first_btn.setStyleSheet(_PILL_STYLE_SELECTED)

    def _on_algo_clicked(self, btn_id: int):
        """算法按钮点击切换"""
        algos = AlgorithmRegistry.all_algorithms()
        if not (0 <= btn_id < len(algos)):
            return

        for i in range(len(algos)):
            btn = self._btn_group.button(i)
            if btn:
                btn.setStyleSheet(
                    _PILL_STYLE_SELECTED if i == btn_id
                    else _PILL_STYLE_UNSELECTED
                )

        desc = algos[btn_id]
        self._current_algo_id = desc.id
        self._build_params(desc)

    def _build_params(self, descriptor):
        """根据 descriptor 动态构建参数控件"""
        self._clear_param_widgets()
        self._params.clear()
        self._combos.clear()

        for p in descriptor.params:
            if p.type == "choice":
                self._add_choice_param(p)
            else:
                self._add_slider_param(p)

    def _clear_param_widgets(self):
        """清除参数容器中的所有控件"""
        while self._param_container.count():
            item = self._param_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout):
        """递归清除子布局"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _add_slider_param(self, p: ParamDef):
        slider = ParamSlider(p)
        self._param_container.addWidget(slider)
        self._params[p.name] = slider

    def _add_choice_param(self, p: ParamDef):
        row = QHBoxLayout()
        row.setSpacing(6)

        label = QLabel(p.label)
        label.setFixedWidth(58)
        label.setStyleSheet("color: #aaa; font-size: 11px;")
        row.addWidget(label)

        combo = QComboBox()
        combo.addItems(p.choices)
        row.addWidget(combo, stretch=1)

        self._param_container.addLayout(row)
        self._combos[p.name] = combo

    def _on_apply(self):
        if self._current_algo_id:
            self.apply_requested.emit(self._current_algo_id)

    def _on_reset(self):
        if self._current_algo_id:
            desc = self._descriptors.get(self._current_algo_id)
            if desc:
                self._build_params(desc)
            self.reset_requested.emit(self._current_algo_id)

    def current_algo_id(self) -> str:
        """获取当前选中的算法 ID"""
        return self._current_algo_id or ""

    def get_current_params(self) -> dict:
        """
        收集当前所有参数值，返回 {name: value} 字典

        对于 choice 类型，返回当前选中的字符串值。
        对于 Retinex 的 sigma_list 参数，会做特殊处理合并多个 sigma 滑块。
        """
        if not self._current_algo_id:
            return {}

        params = {}
        for name, slider in self._params.items():
            val = slider.value()
            if slider._param.type == "int":
                val = int(val)
            params[name] = val

        for name, combo in self._combos.items():
            params[name] = combo.currentText()

        # Retinex 特殊处理: 合并 sigma_list
        if self._current_algo_id == "retinex":
            mode = params.get("mode", "msr")
            if mode == "msr":
                s1 = params.pop("sigma_list", 15)
                s2 = params.pop("sigma_list_2", 80)
                s3 = params.pop("sigma_list_3", 250)
                params["sigma_list"] = (int(s1), int(s2), int(s3))
            else:
                s = params.pop("sigma_list", 80)
                params.pop("sigma_list_2", None)
                params.pop("sigma_list_3", None)
                params["sigma"] = int(s)

        return params
