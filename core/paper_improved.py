"""
暗通道改进去雾算法
"""

import cv2
import numpy as np

from core.dark_channel import (
    compute_dark_channel, recover_scene
)
from core.guided_filter import guided_filter


def _compute_adaptive_patch_size(image: np.ndarray) -> int:
    """
    基于图像梯度统计自适应计算暗通道模板尺寸
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    # Sobel 梯度
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mean = np.mean(np.sqrt(grad_x ** 2 + grad_y ** 2))

    # 自适应计算
    size = int(31 - grad_mean / 3.0)
    size = max(7, min(31, size))
    # 确保为奇数
    if size % 2 == 0:
        size += 1
    return size


def _estimate_atmospheric_light_improved(
    image: np.ndarray,
    dark_channel: np.ndarray
) -> np.ndarray:
    """
    改进大气光估计 — 阈值法去除高亮区域干扰
    """
    h, w = dark_channel.shape
    img_float = image.astype(np.float64)

    # 计算亮度
    brightness = np.max(img_float, axis=2)

    # 亮度阈值: 排除过亮区域
    threshold = np.where(brightness <= 160, 4.0 * brightness / 3.0, 255.0)

    # 检测 RGB 三通道值相近的高亮像素（白色物体干扰）
    r, g, b = img_float[:, :, 2], img_float[:, :, 1], img_float[:, :, 0]
    max_diff = np.maximum(np.maximum(np.abs(r - g), np.abs(g - b)), np.abs(r - b))
    # 三通道差值小于阈值且亮度高于阈值的像素，认为是白色物体
    white_mask = (max_diff < 30) & (brightness > 200)

    # 修正暗通道：将白色物体区域暗通道置零
    dark_corrected = dark_channel.astype(np.float64).copy()
    dark_corrected[white_mask] = 0

    # 排除超过亮度阈值的像素
    dark_corrected[brightness > threshold] = 0

    # 在修正后的暗通道上取最亮的 top 0.1% 像素
    num_pixels = h * w
    num_brightest = max(int(num_pixels * 0.001), 1)
    flat_dark = dark_corrected.flatten()
    indices = np.argpartition(flat_dark, -num_brightest)[-num_brightest:]

    rows, cols = np.unravel_index(indices, (h, w))
    atmospheric_light = img_float[rows, cols].mean(axis=0)

    return atmospheric_light


def _estimate_transmission_improved(
    image: np.ndarray,
    atmospheric_light: np.ndarray,
    patch_size: int,
    omega: float
) -> np.ndarray:
    """
    改进透射率估计 — 天空区域透射率修正
    """
    img = image.astype(np.float64)

    # 标准透射率估计
    normalized = img / atmospheric_light
    min_channel = np.min(normalized, axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (patch_size, patch_size))
    dark = cv2.erode(min_channel, kernel)
    transmission = 1.0 - omega * dark

    # 天空区域修正: t(x) > 1 时使用修正公式
    # t(x) = min_c(1 - I^c(x) / A^c)
    sky_mask = transmission > 1.0
    if np.any(sky_mask):
        # 逐通道计算修正透射率
        corrected_t = np.min(1.0 - img / atmospheric_light, axis=2)
        corrected_t = np.clip(corrected_t, 0, 1)
        transmission[sky_mask] = corrected_t[sky_mask]

    # 确保透射率在合理范围
    transmission = np.clip(transmission, 0, 1)
    return transmission


def paper_improved_dehaze(
    image: np.ndarray,
    omega: float = 0.95,
    t_min: float = 0.1,
    guided_radius: int = 8,
    guided_eps: float = 0.01
) -> np.ndarray:
    """
    论文改进算法入口函数
    """
    # 改进 1: 自适应模板尺寸
    patch_size = _compute_adaptive_patch_size(image)

    # 改进 2: 改进大气光估计
    dark = compute_dark_channel(image, patch_size)
    A = _estimate_atmospheric_light_improved(image, dark)

    # 改进 3: 改进透射率估计
    t_coarse = _estimate_transmission_improved(image, A, patch_size, omega)

    # 引导滤波细化透射率
    guide = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    t_refined = guided_filter(guide, t_coarse, guided_radius, guided_eps)
    t_refined = np.clip(t_refined, 0, 1)

    # 场景恢复
    result = recover_scene(image, t_refined, A, t_min)

    return result


# ================================================================
#  算法注册
# ================================================================

from core.registry import AlgorithmRegistry, AlgorithmDescriptor, ParamDef

AlgorithmRegistry.register(AlgorithmDescriptor(
    id="paper_improved",
    name="暗通道改进",
    description="自适应模板 + 改进大气光估计 + 天空区域透射率修正",
    category="improved",
    func=paper_improved_dehaze,
    params=[
        ParamDef(name="omega", label="去雾强度", type="float",
                 min_val=0.5, max_val=1.0, default=0.95, step=0.01, decimals=2),
        ParamDef(name="t_min", label="透射率下界", type="float",
                 min_val=0.01, max_val=0.3, default=0.1, step=0.01, decimals=2),
        ParamDef(name="guided_radius", label="滤波半径", type="int",
                 min_val=1, max_val=30, default=8, step=1, decimals=0),
        ParamDef(name="guided_eps", label="正则化", type="float",
                 min_val=0.001, max_val=0.1, default=0.01, step=0.001, decimals=3),
    ]
))
