"""
Retinex 去雾算法

基于 Retinex 理论的图像去雾，核心思想是通过对数域运算分离图像的
照度分量（illumination）和反射率分量（reflectance）。
"""

import cv2
import numpy as np


def _gaussian_blur(image: np.ndarray, sigma: float) -> np.ndarray:
    """
    高斯模糊（用于估计照度分量）
    """
    # 根据 sigma 自动计算核大小（通常取 6σ+1）
    ksize = int(np.ceil(sigma * 6) + 1)
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(image, (ksize, ksize), sigma)


def single_scale_retinex(
    image: np.ndarray,
    sigma: float = 80.0
) -> np.ndarray:
    """
    单尺度 Retinex (SSR)
    """
    img = image.astype(np.float64) + 1.0  # +1 避免对数零

    result = np.zeros_like(img)
    for c in range(3):
        channel = img[:, :, c]
        # 估计照度分量
        illumination = _gaussian_blur(channel, sigma)
        # Retinex 公式: log(R) = log(I) - log(L)
        log_retinex = np.log(channel) - np.log(illumination)
        result[:, :, c] = log_retinex

    # 使用 CRF 归一化
    result = _normalize_retinex(result, image)
    return result


def multi_scale_retinex(
    image: np.ndarray,
    sigma_list: tuple = (15, 80, 250)
) -> np.ndarray:
    """
    多尺度 Retinex (MSR)
    """
    img = image.astype(np.float64) + 1.0

    num_scales = len(sigma_list)
    weight = 1.0 / num_scales  # 等权重

    msr_result = np.zeros_like(img)
    for c in range(3):
        channel = img[:, :, c]
        channel_msr = np.zeros(channel.shape, dtype=np.float64)
        for sigma in sigma_list:
            illumination = _gaussian_blur(channel, sigma)
            log_retinex = np.log(channel) - np.log(illumination)
            channel_msr += weight * log_retinex
        msr_result[:, :, c] = channel_msr

    # 使用 CRF 归一化
    result = _normalize_retinex(msr_result, image)
    return result


def _normalize_retinex(retinex: np.ndarray, original: np.ndarray) -> np.ndarray:
    """
    使用 CRF（色彩恢复因子）归一化 Retinex 输出
    """
    # 计算色彩恢复因子 (Color Restoration Function)
    img = original.astype(np.float64) + 1.0
    sum_channels = np.sum(img, axis=2, keepdims=True)
    crf = np.log(125.0 * img / sum_channels)

    # 应用 CRF
    restored = retinex * crf

    # Gain/Offset 归一化
    mean_val = restored.mean()
    std_val = restored.std()
    result = (restored - mean_val) / (std_val + 1e-6) * 50 + 128

    return np.clip(result, 0, 255).astype(np.uint8)


def retinex_dehaze(
    image: np.ndarray,
    mode: str = "msr",
    sigma: float = 80.0,
    sigma_list: tuple = (15, 80, 250)
) -> np.ndarray:
    """
    Retinex 去雾入口函数
    """
    if mode == "ssr":
        return single_scale_retinex(image, sigma)
    elif mode == "msr":
        return multi_scale_retinex(image, sigma_list)
    else:
        raise ValueError(f"不支持的 Retinex 模式: {mode}，请使用 'ssr' 或 'msr'")


# ================================================================
#  算法注册
# ================================================================

from core.registry import AlgorithmRegistry, AlgorithmDescriptor, ParamDef

AlgorithmRegistry.register(AlgorithmDescriptor(
    id="retinex",
    name="Retinex 去雾",
    description="基于 Retinex 理论的对数域去雾方法",
    category="enhancement",
    func=retinex_dehaze,
    params=[
        ParamDef(name="mode", label="Retinex 模式", type="choice",
                 default=0, choices=["msr", "ssr"]),
        ParamDef(name="sigma_list", label="sigma_1", type="int",
                 min_val=1, max_val=300, default=15, step=1, decimals=0),
        ParamDef(name="sigma_list_2", label="sigma_2", type="int",
                 min_val=1, max_val=300, default=80, step=1, decimals=0),
        ParamDef(name="sigma_list_3", label="sigma_3", type="int",
                 min_val=1, max_val=300, default=250, step=1, decimals=0),
    ]
))
