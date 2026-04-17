"""
三区域分区改进 DCP 去雾算法

在标准暗通道先验 (DCP) 的基础上，引入天空区域检测和明亮区域检测，
对图像进行三区域分区处理，避免天空和明亮区域的过处理问题。
"""

import cv2
import numpy as np

from core.dark_channel import (
    compute_dark_channel, estimate_atmospheric_light,
    estimate_transmission, recover_scene
)
from core.guided_filter import guided_filter


def detect_sky_region(
    image: np.ndarray,
    dark_channel: np.ndarray,
    threshold_ratio: float = 0.9
) -> np.ndarray:
    """
    天空区域检测
    """
    # 计算亮度（取三通道最大值）
    brightness = np.max(image.astype(np.float64), axis=2)

    # 归一化到 [0, 1]
    brightness_norm = brightness / 255.0
    dark_norm = dark_channel.astype(np.float64) / 255.0

    # 天空区域：亮度高 + 暗通道值大
    sky_mask = (brightness_norm > threshold_ratio) & (dark_norm > threshold_ratio)

    # 形态学后处理：先膨胀再腐蚀，去除噪声和小孔
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    sky_mask_uint8 = sky_mask.astype(np.uint8) * 255
    sky_mask_uint8 = cv2.morphologyEx(sky_mask_uint8, cv2.MORPH_CLOSE, kernel)
    sky_mask_uint8 = cv2.morphologyEx(sky_mask_uint8, cv2.MORPH_OPEN, kernel)

    return sky_mask_uint8 > 127


def detect_bright_region(
    image: np.ndarray,
    brightness_threshold: float = 220.0
) -> np.ndarray:
    """
    明亮区域检测（非天空部分）
    """
    # 三通道均值作为亮度
    brightness = np.mean(image.astype(np.float64), axis=2)
    bright_mask = brightness > brightness_threshold

    # 形态学后处理
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    bright_mask_uint8 = bright_mask.astype(np.uint8) * 255
    bright_mask_uint8 = cv2.morphologyEx(bright_mask_uint8, cv2.MORPH_CLOSE, kernel)

    return bright_mask_uint8 > 127


def improved_dehaze(
    image: np.ndarray,
    patch_size: int = 15,
    guided_radius: int = 8,
    guided_eps: float = 0.01,
    omega: float = 0.95,
    t_min: float = 0.1,
    sky_threshold: float = 0.9,
    bright_threshold: float = 220.0
) -> np.ndarray:
    """
    三区域分区改进 DCP 去雾
    """
    # Step 1: 计算暗通道和大气光
    dark = compute_dark_channel(image, patch_size)
    A = estimate_atmospheric_light(image, dark)

    # Step 2: 检测天空和明亮区域
    sky_mask = detect_sky_region(image, dark, sky_threshold)
    bright_mask = detect_bright_region(image, bright_threshold)
    # 明亮区域需要排除天空部分
    bright_mask = bright_mask & (~sky_mask)

    # Step 3: 计算全图透射率（普通区域用完整 omega）
    transmission_full = estimate_transmission(image, A, patch_size, omega)

    # 使用引导滤波细化透射率
    guide = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    t_refined = guided_filter(guide, transmission_full, guided_radius, guided_eps)
    t_refined = np.clip(t_refined, 0, 1)

    # Step 4: 计算低强度透射率（明亮区域用）
    omega_low = omega * 0.4  # 明亮区域去雾强度降低
    transmission_low = estimate_transmission(image, A, patch_size, omega_low)
    t_low_refined = guided_filter(guide, transmission_low, guided_radius, guided_eps)
    t_low_refined = np.clip(t_low_refined, 0, 1)

    # Step 5: 按区域恢复场景
    # 普通区域：正常恢复
    result_full = recover_scene(image, t_refined, A, t_min)
    # 明亮区域：轻度恢复
    result_low = recover_scene(image, t_low_refined, A, t_min)
    # 天空区域：保持原图
    result_img = image.astype(np.float64).copy()

    # 构建三区域融合
    sky_mask_3c = np.stack([sky_mask] * 3, axis=2)
    bright_mask_3c = np.stack([bright_mask] * 3, axis=2)

    result_img[~sky_mask_3c & ~bright_mask_3c] = result_full.astype(np.float64)[~sky_mask_3c & ~bright_mask_3c]
    result_img[bright_mask_3c] = result_low.astype(np.float64)[bright_mask_3c]
    # 天空区域保持原图，不处理

    # Step 6: 区域边界平滑（使用高斯模糊实现平滑过渡）
    result_final = _smooth_boundary(
        result_img,
        sky_mask.astype(np.float64),
        bright_mask.astype(np.float64),
        image.astype(np.float64),
        result_full.astype(np.float64),
        result_low.astype(np.float64)
    )

    return np.clip(result_final, 0, 255).astype(np.uint8)


def _smooth_boundary(
    result: np.ndarray,
    sky_mask: np.ndarray,
    bright_mask: np.ndarray,
    original: np.ndarray,
    result_normal: np.ndarray,
    result_low: np.ndarray
) -> np.ndarray:
    """
    区域边界平滑融合
    """
    # 对掩码进行高斯模糊，产生平滑的权重
    sky_weight = cv2.GaussianBlur(sky_mask, (31, 31), 0)
    bright_weight = cv2.GaussianBlur(bright_mask, (15, 15), 0)

    # 确保权重和 <= 1
    total_weight = np.clip(sky_weight + bright_weight, 0, 1)
    normal_weight = 1.0 - total_weight

    # 三通道权重
    sky_w3 = sky_weight[:, :, np.newaxis]
    bright_w3 = bright_weight[:, :, np.newaxis]
    normal_w3 = normal_weight[:, :, np.newaxis]

    # 加权融合
    blended = (
        sky_w3 * original +
        bright_w3 * result_low +
        normal_w3 * result_normal
    )

    return blended


# ================================================================
#  算法注册
# ================================================================

from core.registry import AlgorithmRegistry, AlgorithmDescriptor, ParamDef

AlgorithmRegistry.register(AlgorithmDescriptor(
    id="improved_dcp",
    name="三区域改进 DCP",
    description="天空/明亮/普通分区策略，避免过处理",
    category="improved",
    func=improved_dehaze,
    params=[
        ParamDef(name="patch_size", label="窗口大小", type="int",
                 min_val=3, max_val=31, default=15, step=2, decimals=0,
                 odd_only=True),
        ParamDef(name="guided_radius", label="滤波半径", type="int",
                 min_val=1, max_val=30, default=8, step=1, decimals=0),
        ParamDef(name="guided_eps", label="正则化", type="float",
                 min_val=0.001, max_val=0.1, default=0.01, step=0.001, decimals=3),
        ParamDef(name="omega", label="去雾强度", type="float",
                 min_val=0.5, max_val=1.0, default=0.95, step=0.01, decimals=2),
        ParamDef(name="t_min", label="透射率下界", type="float",
                 min_val=0.01, max_val=0.3, default=0.1, step=0.01, decimals=2),
        ParamDef(name="sky_threshold", label="天空阈值", type="float",
                 min_val=0.5, max_val=1.0, default=0.9, step=0.01, decimals=2),
        ParamDef(name="bright_threshold", label="明亮阈值", type="float",
                 min_val=150, max_val=255, default=220, step=1, decimals=0),
    ]
))
