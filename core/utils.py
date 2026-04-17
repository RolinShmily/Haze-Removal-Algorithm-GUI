"""
工具函数
numpy_to_qpixmap、to_gray、ensure_uint8、ensure_float 等通用工具
"""

from PySide6.QtGui import QPixmap, QImage
import numpy as np


def numpy_to_qpixmap(image: np.ndarray) -> QPixmap:
    """
    将 numpy/OpenCV 图像转换为 QPixmap
    """
    if image is None:
        return QPixmap()

    if len(image.shape) == 2:
        # 灰度图像
        h, w = image.shape
        bytes_per_line = w
        q_img = QImage(image.data, w, h, bytes_per_line,
                       QImage.Format_Grayscale8)
    elif image.shape[2] == 4:
        # BGRA -> RGBA
        rgba = image[:, :, [2, 1, 0, 3]].copy()
        h, w, ch = rgba.shape
        bytes_per_line = ch * w
        q_img = QImage(rgba.data, w, h, bytes_per_line,
                       QImage.Format_RGBA8888)
    else:
        # BGR -> RGB
        rgb = image[:, :, ::-1].copy()
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line,
                       QImage.Format_RGB888)

    return QPixmap.fromImage(q_img)


def to_gray(image: np.ndarray) -> np.ndarray:
    """将图像转为灰度"""
    if len(image.shape) == 2:
        return image
    return np.mean(image[:, :, :3], axis=2).astype(np.uint8)


def ensure_uint8(image: np.ndarray) -> np.ndarray:
    """确保图像为 uint8 类型"""
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def ensure_float(image: np.ndarray) -> np.ndarray:
    """确保图像为 float64 类型，范围 [0, 255]"""
    if image.dtype != np.float64:
        return image.astype(np.float64)
    return image.copy()


def compute_histogram(image: np.ndarray) -> np.ndarray:
    """计算灰度直方图（256 bins），使用 np.bincount 向量化计算"""
    gray = to_gray(image)
    return np.bincount(gray.ravel(), minlength=256).astype(np.int64)


def compute_histogram_bgr(image: np.ndarray):
    """计算 BGR 三通道直方图，使用 np.bincount 向量化计算"""
    b_hist = np.bincount(image[:, :, 0].ravel(), minlength=256).astype(np.int64)
    g_hist = np.bincount(image[:, :, 1].ravel(), minlength=256).astype(np.int64)
    r_hist = np.bincount(image[:, :, 2].ravel(), minlength=256).astype(np.int64)
    return b_hist, g_hist, r_hist
