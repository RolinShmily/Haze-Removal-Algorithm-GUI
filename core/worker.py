"""
线程管理模块

提供安全的后台任务执行机制，解决原版中 QThread 销毁导致的崩溃问题。
"""

import time

from PySide6.QtCore import QThread, Signal, QObject


class PreviewWorker(QThread):
    """
    后台预览工作线程
    """

    finished = Signal(object, float, str, int)  # result, elapsed_ms, algo_name, seq
    error = Signal(str, str, int)               # error_msg, algo_name, seq

    def __init__(self, func, image, kwargs, algo_name: str, seq: int):
        super().__init__()
        self.func = func
        self.image = image
        self.kwargs = kwargs
        self.algo_name = algo_name
        self.seq = seq

    def run(self):
        try:
            t0 = time.perf_counter()
            result = self.func(self.image, **self.kwargs)
            elapsed = (time.perf_counter() - t0) * 1000
            self.finished.emit(result, elapsed, self.algo_name, self.seq)
        except Exception as e:
            self.error.emit(str(e), self.algo_name, self.seq)


class WorkerManager(QObject):
    """
    线程管理器
    """

    preview_success = Signal(object, float, str)
    preview_error = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers = []   # 保留引用，防止 GC 回收运行中的线程
        self._seq = 0        # 递增序号，用于过滤过期结果

    def submit(self, func, image, kwargs, algo_name: str) -> None:
        """
        提交一个新任务
        """
        # 递增序号，使之前所有 worker 结果作废
        self._seq += 1
        seq = self._seq

        # 清理已结束的 worker 释放引用
        self._cleanup_workers()

        # 创建并启动新 worker
        worker = PreviewWorker(func, image, kwargs, algo_name, seq)
        worker.finished.connect(self._on_finished)
        worker.error.connect(self._on_error)
        self._workers.append(worker)
        worker.start()

    def invalidate(self) -> None:
        """递增序号使所有正在运行的结果作废"""
        self._seq += 1

    def shutdown(self, timeout: int = 3000) -> None:
        """
        等待所有线程结束（在 closeEvent 中调用）

        Args:
            timeout: 单个线程最大等待时间（毫秒）
        """
        for w in self._workers:
            if w.isRunning():
                w.wait(timeout)
        self._workers.clear()

    def _on_finished(self, result, elapsed_ms, algo_name, seq):
        """Worker 完成 — 只转发最新序号的结果"""
        if seq == self._seq:
            self.preview_success.emit(result, elapsed_ms, algo_name)

    def _on_error(self, error_msg, algo_name, seq):
        """Worker 出错 — 只转发最新序号的错误"""
        if seq == self._seq:
            self.preview_error.emit(error_msg, algo_name)

    def _cleanup_workers(self):
        """清理已结束的 worker，释放引用"""
        self._workers = [w for w in self._workers if w.isRunning()]
