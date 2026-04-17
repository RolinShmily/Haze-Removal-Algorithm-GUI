"""
应用控制器

MainWindow 只负责 UI 布局和信号转发，本控制器处理所有业务逻辑。
"""

import os

import numpy as np
import cv2

from PySide6.QtCore import QObject, Signal, Slot

from core.registry import AlgorithmRegistry
from core.worker import WorkerManager
from core.metrics import compute_metrics
from core.evaluation import compute_evaluation


class AppController(QObject):
    """
    应用控制器 — 业务逻辑层
    """

    display_updated = Signal(object, object)
    metrics_updated = Signal(dict)
    evaluation_updated = Signal(dict)
    status_message = Signal(str)
    log_message = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 图像状态
        self._original_image = None
        self._current_image = None
        self._result_image = None

        # 操作历史
        self._history = []
        self._max_history = 20

        # 上次处理耗时
        self._last_elapsed_ms = None
        self._is_processing = False

        # WorkerManager
        self._worker_mgr = WorkerManager(self)
        self._worker_mgr.preview_success.connect(self._on_preview_success)
        self._worker_mgr.preview_error.connect(self._on_preview_error)

    # ================================================================
    #  公共接口
    # ================================================================

    def load_image(self, file_path: str) -> None:
        """加载图像文件"""
        img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            self.log_message.emit("无法读取图像文件", "ERR")
            return

        self._original_image = img.copy()
        self._current_image = img.copy()
        self._result_image = None
        self._last_elapsed_ms = None
        self._history.clear()

        self._emit_display_update()
        self._emit_metrics_update()
        self._update_status()

        h, w = img.shape[:2]
        self.log_message.emit(
            f"已加载图像: {os.path.basename(file_path)} ({w}x{h})", "OK"
        )

    def save_result(self, file_path: str) -> None:
        """保存结果图像"""
        if self._result_image is None:
            self.log_message.emit("暂无处理结果可保存", "WARN")
            return

        ext = os.path.splitext(file_path)[1]
        success, encoded = cv2.imencode(ext, self._result_image)
        if success:
            encoded.tofile(file_path)
            self.log_message.emit(f"已保存: {os.path.basename(file_path)}", "OK")
        else:
            self.log_message.emit("保存失败", "ERR")

    def reset_to_original(self) -> None:
        """重置为原图"""
        if self._original_image is None:
            return
        self._push_history("重置前状态")
        self._current_image = self._original_image.copy()
        self._result_image = None
        self._last_elapsed_ms = None
        self._emit_display_update()
        self._emit_metrics_update()
        self._update_status()
        self.log_message.emit("已重置为原图", "INFO")

    def apply_result(self) -> None:
        """将当前预览结果应用到当前图像"""
        if self._result_image is None:
            return
        self._push_history("应用前状态")
        self._current_image = self._result_image.copy()
        self._result_image = None
        self._last_elapsed_ms = None
        self._emit_display_update()
        self._emit_metrics_update()
        self._update_status()
        self.log_message.emit("已将结果应用到当前图像", "OK")

    def undo(self) -> None:
        """撤销"""
        if not self._history:
            return
        img, desc = self._history.pop()
        self._current_image = img
        self._result_image = None
        self._last_elapsed_ms = None
        self._emit_display_update()
        self._emit_metrics_update()
        self._update_status()
        self.log_message.emit(f"已撤销: {desc}", "INFO")

    def has_image(self) -> bool:
        """是否已加载图像"""
        return self._current_image is not None

    def has_result(self) -> bool:
        """是否有处理结果"""
        return self._result_image is not None

    def has_history(self) -> bool:
        """是否有可撤销的历史"""
        return len(self._history) > 0

    def history_count(self) -> int:
        """历史步数"""
        return len(self._history)

    def current_image(self):
        """获取当前图像"""
        return self._current_image

    def result_image(self):
        """获取结果图像"""
        return self._result_image

    def shutdown(self) -> None:
        """关闭时等待所有线程结束"""
        self._worker_mgr.shutdown(timeout=3000)

    # ================================================================
    #  手动应用处理
    # ================================================================

    def apply_processing(self) -> None:
        """手动触发处理 — 由用户点击"应用"按钮调用"""
        if self._current_image is None:
            self.log_message.emit("请先打开图像", "WARN")
            return

        algo_id = self._get_current_algo_id()
        if not algo_id:
            return

        desc = AlgorithmRegistry.get(algo_id)
        if desc is None:
            return

        # 收集参数
        params = self._collect_params_callback()
        if params is None:
            return

        self._is_processing = True
        self._update_status()
        self.log_message.emit(f"[{desc.name}] 开始处理...", "PROC")

        # 记录参数到日志
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        self.log_message.emit(f"  {param_str}", "INFO")

        # 提交到 WorkerManager
        self._worker_mgr.submit(
            desc.func,
            self._current_image.copy(),
            params,
            desc.name
        )

    def reset_preview(self, algo_id: str) -> None:
        """重置参数时清除预览"""
        self._worker_mgr.invalidate()
        self._is_processing = False
        self._result_image = None
        self._last_elapsed_ms = None
        self._emit_display_update()
        self._emit_metrics_update()
        self.log_message.emit("参数已重置", "INFO")

    # ================================================================
    #  参数收集回调
    # ================================================================

    def set_collect_params_callback(self, fn) -> None:
        """设置参数收集回调（由 MainWindow 在连接信号时设置）"""
        self._collect_params_callback = fn

    def _collect_params_callback(self) -> dict:
        """默认参数收集（应被 set_collect_params_callback 覆盖）"""
        return {}

    def set_current_algo_id_fn(self, fn) -> None:
        """设置获取当前算法 ID 的回调"""
        self._get_current_algo_id = fn

    def _get_current_algo_id(self) -> str:
        """默认返回空字符串（应被 set_current_algo_id_fn 覆盖）"""
        return ""

    # ================================================================
    #  Worker 回调
    # ================================================================

    @Slot(object, float, str)
    def _on_preview_success(self, result, elapsed_ms, algo_name):
        """后台处理完成"""
        self._is_processing = False
        self._result_image = result
        self._last_elapsed_ms = elapsed_ms

        self._emit_display_update()
        self._emit_metrics_update()
        self._emit_evaluation_update()
        self._update_status(elapsed_ms=elapsed_ms)

        h, w = result.shape[:2]
        self.log_message.emit(
            f"[{algo_name}] 完成  |  {w}x{h}  |  {elapsed_ms:.0f}ms", "OK"
        )

    @Slot(str, str)
    def _on_preview_error(self, error_msg, algo_name):
        """后台处理出错"""
        self._is_processing = False
        self._update_status()
        self.log_message.emit(f"[{algo_name}] 错误: {error_msg}", "ERR")

    # ================================================================
    #  内部辅助
    # ================================================================

    def _push_history(self, description: str) -> None:
        """保存当前状态到历史"""
        if self._current_image is None:
            return
        self._history.append((self._current_image.copy(), description))
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def _emit_display_update(self) -> None:
        """发送显示更新信号"""
        self.display_updated.emit(self._current_image, self._result_image)

    def _emit_metrics_update(self) -> None:
        """发送指标更新信号"""
        if self._current_image is not None and self._result_image is not None:
            try:
                metrics = compute_metrics(self._current_image, self._result_image)
                metrics["elapsed_ms"] = self._last_elapsed_ms
                self.metrics_updated.emit(metrics)
            except Exception:
                self.metrics_updated.emit({"elapsed_ms": self._last_elapsed_ms})
        else:
            self.metrics_updated.emit({})

    def _emit_evaluation_update(self) -> None:
        """发送论文评价指标更新信号"""
        if self._current_image is not None and self._result_image is not None:
            try:
                evaluation = compute_evaluation(self._current_image, self._result_image)
                self.evaluation_updated.emit(evaluation)
            except Exception:
                self.evaluation_updated.emit({})

    def _update_status(self, elapsed_ms=None) -> None:
        """更新状态栏信息"""
        img = self._current_image
        if img is None:
            self.status_message.emit("就绪 - 请打开图像文件 (Ctrl+O) 或拖拽图像到窗口")
            return

        h, w = img.shape[:2]
        ch = img.shape[2] if len(img.shape) == 3 else 1
        ch_name = "BGR" if ch == 3 else ("BGRA" if ch == 4 else "灰度")
        msg = f"{w}x{h}  |  {ch_name}  |  历史 {len(self._history)} 步"
        if elapsed_ms is not None:
            msg += f"  |  {elapsed_ms:.0f}ms"
        if self._is_processing:
            msg = "处理中...  |  " + msg
        self.status_message.emit(msg)
