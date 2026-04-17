"""
CLAHE 去雾算法

基于对比度受限自适应直方图均衡化 (Contrast Limited Adaptive Histogram Equalization)
实现图像去雾增强。
"""

import cv2
import numpy as np


def clahe_dehaze(
    image: np.ndarray,
    clip_limit: float = 3.0,
    tile_grid_size: int = 8,
    sharpen: bool = True
) -> np.ndarray:
    """
    CLAHE 去雾处理

    处理流程:
        1. BGR -> LAB 颜色空间转换
        2. 对 L（亮度）通道应用 CLAHE
        3. 合并通道后转回 BGR
        4. 可选: Unsharp Mask 锐化增强细节
    """
    # Step 1: 转换到 LAB 颜色空间
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Step 2: 分离 L、A、B 通道
    l_channel, a_channel, b_channel = cv2.split(lab)

    # Step 3: 对 L 通道应用 CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=(tile_grid_size, tile_grid_size)
    )
    l_enhanced = clahe.apply(l_channel)

    # Step 4: 合并通道并转回 BGR
    lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    # Step 5: 可选的 Unsharp Mask 锐化
    if sharpen:
        result = _unsharp_mask(result)

    return result


def _unsharp_mask(
    image: np.ndarray,
    sigma: float = 1.0,
    amount: float = 0.5
) -> np.ndarray:
    """
    Unsharp Mask 锐化
    """
    blurred = cv2.GaussianBlur(image, (0, 0), sigma)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


# ================================================================
#  算法注册
# ================================================================

from core.registry import AlgorithmRegistry, AlgorithmDescriptor, ParamDef

AlgorithmRegistry.register(AlgorithmDescriptor(
    id="clahe",
    name="CLAHE 去雾",
    description="LAB 空间 L 通道自适应直方图均衡化",
    category="enhancement",
    func=clahe_dehaze,
    params=[
        ParamDef(name="clip_limit", label="对比度限制", type="float",
                 min_val=1, max_val=10, default=3.0, step=0.1, decimals=1),
        ParamDef(name="tile_grid_size", label="分区大小", type="int",
                 min_val=2, max_val=16, default=8, step=1, decimals=0),
    ]
))
