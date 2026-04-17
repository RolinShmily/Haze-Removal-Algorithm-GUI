"""
引导滤波 (Guided Filter)

基于 He et al. (2010) 的引导滤波算法。
引导滤波是一种局部线性模型滤波器，可用于：
    - 边缘保持平滑
    - 细节增强
    - 替代 soft matting 进行透射率细化
"""

import cv2
import numpy as np


def guided_filter(
    guide: np.ndarray,
    src: np.ndarray,
    radius: int = 8,
    eps: float = 0.01
) -> np.ndarray:
    """
    引导滤波（灰度引导图版本）
    """
    # 确保输入为 float64
    guide = guide.astype(np.float64)
    src = src.astype(np.float64)

    # 如果是灰度引导图，确保为 2D
    if len(guide.shape) == 3:
        guide = cv2.cvtColor(guide.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float64)

    # 如果是 2D 输入，确保维度
    if len(src.shape) == 3:
        result = np.zeros_like(src)
        for c in range(src.shape[2]):
            result[:, :, c] = _guided_filter_single(guide, src[:, :, c], radius, eps)
        return result
    else:
        return _guided_filter_single(guide, src, radius, eps)


def _guided_filter_single(
    guide: np.ndarray,
    src: np.ndarray,
    radius: int,
    eps: float
) -> np.ndarray:
    """
    单通道引导滤波实现（基于 boxFilter）
    """
    # 窗口大小 (diameter)
    diam = 2 * radius + 1

    # 计算窗口内均值相关统计量
    mean_I = cv2.boxFilter(guide, -1, (diam, diam))
    mean_p = cv2.boxFilter(src, -1, (diam, diam))
    mean_Ip = cv2.boxFilter(guide * src, -1, (diam, diam))
    mean_II = cv2.boxFilter(guide * guide, -1, (diam, diam))

    # 协方差和方差
    cov_Ip = mean_Ip - mean_I * mean_p
    var_I = mean_II - mean_I * mean_I

    # 线性系数 a 和 b
    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I

    # 对 a 和 b 取窗口均值得到最终系数
    mean_a = cv2.boxFilter(a, -1, (diam, diam))
    mean_b = cv2.boxFilter(b, -1, (diam, diam))

    # 输出
    q = mean_a * guide + mean_b
    return q


def guided_filter_bgr(
    guide_bgr: np.ndarray,
    src: np.ndarray,
    radius: int = 8,
    eps: float = 0.01
) -> np.ndarray:
    """
    BGR 彩色引导图的引导滤波
    """
    guide = guide_bgr.astype(np.float64) / 255.0 if guide_bgr.dtype == np.uint8 else guide_bgr.astype(np.float64)
    src_f = src.astype(np.float64)

    # 使用 OpenCV 的 guidedFilter（如果可用）
    try:
        guide_u8 = (guide * 255).astype(np.uint8) if guide.max() <= 1.0 else guide.astype(np.uint8)
        if len(src_f.shape) == 2:
            result = cv2.ximgproc.guidedFilter(guide_u8, src_f, radius, eps)
        else:
            result = np.zeros_like(src_f)
            for c in range(src_f.shape[2]):
                result[:, :, c] = cv2.ximgproc.guidedFilter(
                    guide_u8, src_f[:, :, c], radius, eps
                )
        return result
    except (AttributeError, cv2.error):
        # fallback: 灰度引导
        gray = cv2.cvtColor((guide * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float64) / 255.0
        return guided_filter(gray, src_f, radius, eps)


def dehaze_dcp_guided(
    image: np.ndarray,
    patch_size: int = 15,
    guided_radius: int = 8,
    guided_eps: float = 0.01,
    omega: float = 0.95,
    t_min: float = 0.1
) -> np.ndarray:
    """
    DCP + 引导滤波完整去雾流程
    """
    from core.dark_channel import (
        compute_dark_channel, estimate_atmospheric_light,
        estimate_transmission, recover_scene
    )

    img = image.astype(np.float64)

    # Step 1: 计算暗通道
    dark = compute_dark_channel(image, patch_size)

    # Step 2: 估计大气光
    A = estimate_atmospheric_light(image, dark)

    # Step 3: 估计粗透射率
    t_coarse = estimate_transmission(image, A, patch_size, omega)

    # Step 4: 使用引导滤波细化透射率（以原图为引导图）
    # 将透射率归一化到 [0, 1]
    t_refined = guided_filter(
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64),
        t_coarse,
        radius=guided_radius,
        eps=guided_eps
    )
    # 确保透射率在 [0, 1] 范围内
    t_refined = np.clip(t_refined, 0, 1)

    # Step 5: 场景恢复
    result = recover_scene(image, t_refined, A, t_min)

    return result


# ================================================================
#  算法注册
# ================================================================

from core.registry import AlgorithmRegistry, AlgorithmDescriptor, ParamDef

AlgorithmRegistry.register(AlgorithmDescriptor(
    id="guided_dcp",
    name="引导滤波 DCP",
    description="使用引导滤波替代 soft matting 细化透射率",
    category="physical",
    func=dehaze_dcp_guided,
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
    ]
))
