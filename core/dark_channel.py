"""
暗通道先验去雾算法 (Dark Channel Prior, DCP)

基于 He et al. (2009) 的暗通道先验理论，实现基于大气散射模型的图像去雾。
"""

import cv2
import numpy as np


def compute_dark_channel(image: np.ndarray, patch_size: int = 15) -> np.ndarray:
    """
    计算暗通道
    """
    # 取每个像素的三通道最小值，然后使用腐蚀操作（等价于最小值滤波）加速
    min_channel = np.min(image, axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (patch_size, patch_size))
    dark = cv2.erode(min_channel, kernel)
    return dark


def _compute_dark_channel_fast(image: np.ndarray, patch_size: int = 15) -> np.ndarray:
    """
    快速计算暗通道（使用 OpenCV 腐蚀操作加速）
    """
    # 三通道取最小值
    min_channel = np.min(image, axis=2)
    # 腐蚀操作等价于最小值滤波
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (patch_size, patch_size)
    )
    dark = cv2.erode(min_channel, kernel)
    return dark


def estimate_atmospheric_light(
    image: np.ndarray,
    dark_channel: np.ndarray,
    top_ratio: float = 0.001
) -> np.ndarray:
    """
    估计大气光值 A
    """
    h, w = dark_channel.shape
    num_pixels = h * w
    num_brightest = max(int(num_pixels * top_ratio), 1)

    # 使用 np.argpartition 向量化选取最亮像素（O(N) 而非 O(N log N)）
    flat_dark = dark_channel.flatten()
    indices = np.argpartition(flat_dark, -num_brightest)[-num_brightest:]

    # 取原图中对应位置的像素（纯 numpy 操作，无 Python 循环）
    rows, cols = np.unravel_index(indices, (h, w))
    img_float = image.astype(np.float64)
    atmospheric_light = img_float[rows, cols].mean(axis=0)

    return atmospheric_light


def estimate_transmission(
    image: np.ndarray,
    atmospheric_light: np.ndarray,
    patch_size: int = 15,
    omega: float = 0.95
) -> np.ndarray:
    """
    估计透射率图
    """
    img = image.astype(np.float64)

    # 归一化：每个通道除以对应的大气光值
    normalized = img / atmospheric_light

    # 计算归一化图像的暗通道
    dark = _compute_dark_channel_fast(normalized, patch_size)

    # 计算透射率
    transmission = 1.0 - omega * dark

    return transmission


def recover_scene(
    image: np.ndarray,
    transmission: np.ndarray,
    atmospheric_light: np.ndarray,
    t_min: float = 0.1
) -> np.ndarray:
    """
    场景恢复：从有雾图像中恢复无雾场景
    """
    img = image.astype(np.float64)

    # 限制透射率下界
    t = np.clip(transmission, t_min, 1.0)

    # 恢复场景: J = (I - A) / t + A
    # 将 t 扩展为与图像相同的维度
    t_3d = t[:, :, np.newaxis]
    recovered = (img - atmospheric_light) / t_3d + atmospheric_light

    # 裁剪到有效范围并转回 uint8
    recovered = np.clip(recovered, 0, 255).astype(np.uint8)
    return recovered


def dehaze_dcp(
    image: np.ndarray,
    patch_size: int = 15,
    omega: float = 0.95,
    t_min: float = 0.1
) -> np.ndarray:
    """
    DCP 完整去雾流程（入口函数）
    """
    # Step 1: 计算暗通道
    dark = compute_dark_channel(image, patch_size)

    # Step 2: 估计大气光
    atmospheric_light = estimate_atmospheric_light(image, dark)

    # Step 3: 估计透射率
    transmission = estimate_transmission(
        image, atmospheric_light, patch_size, omega
    )

    # Step 4: 场景恢复
    result = recover_scene(image, transmission, atmospheric_light, t_min)

    return result


# ================================================================
#  算法注册
# ================================================================

from core.registry import AlgorithmRegistry, AlgorithmDescriptor, ParamDef

AlgorithmRegistry.register(AlgorithmDescriptor(
    id="dcp",
    name="暗通道先验",
    description="基于大气散射模型的物理去雾方法",
    category="physical",
    func=dehaze_dcp,
    params=[
        ParamDef(name="patch_size", label="窗口大小", type="int",
                 min_val=3, max_val=31, default=15, step=2, decimals=0,
                 odd_only=True),
        ParamDef(name="omega", label="去雾强度", type="float",
                 min_val=0.5, max_val=1.0, default=0.95, step=0.01, decimals=2),
        ParamDef(name="t_min", label="透射率下界", type="float",
                 min_val=0.01, max_val=0.3, default=0.1, step=0.01, decimals=2),
    ]
))
