"""
评价指标
"""

import numpy as np
from scipy.ndimage import uniform_filter


def _to_hsi(image: np.ndarray):
    """
    将 BGR 图像转换为 HSI 空间
    """
    bgr = image.astype(np.float64) / 255.0
    b, g, r = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]

    # 亮度 I
    I = (r + g + b) / 3.0

    # 饱和度 S
    min_rgb = np.minimum(np.minimum(r, g), b)
    S = np.where(I > 0, 1.0 - min_rgb / (I + 1e-10), 0.0)

    # 色调 H
    num = 0.5 * ((r - g) + (r - b))
    den = np.sqrt((r - g) ** 2 + (r - b) * (g - b) + 1e-10)
    theta = np.arccos(np.clip(num / den, -1, 1))
    H = np.where(b <= g, theta, 2 * np.pi - theta)
    H = np.degrees(H)

    return H, S, I


def compute_contrast_sigma(processed: np.ndarray) -> float:
    """
    计算对比度指标 sigma — 灰度标准差
    """
    gray = np.mean(processed.astype(np.float64)[:, :, :3], axis=2)
    return float(np.std(gray))


def compute_hue_fidelity(original: np.ndarray, processed: np.ndarray) -> float:
    """
    计算色调还原指标 d — HSI 空间 H 分量相似度
    """
    H_orig, _, _ = _to_hsi(original)
    H_proc, _, _ = _to_hsi(processed)
    diff = np.abs(H_orig - H_proc)
    # 处理色调环形的特性: 差值最大 180
    diff = np.minimum(diff, 360 - diff)
    d = 1.0 - np.mean(diff) / 180.0
    return float(np.clip(d, 0, 1))


def compute_valid_detail(processed: np.ndarray, threshold: float = 10.0) -> float:
    """
    计算有效细节指标 I_valid — 有效梯度占比
    """
    gray = np.mean(processed.astype(np.float64)[:, :, :3], axis=2)
    grad_x = np.diff(gray, axis=1)
    grad_y = np.diff(gray, axis=0)

    # 计算梯度幅值（忽略边界差一像素的问题，取有效区域）
    h, w = gray.shape
    grad_mag = np.zeros((h, w))
    grad_mag[:h - 1, :w - 1] = np.sqrt(grad_x[:h - 1, :] ** 2 + grad_y[:, :w - 1] ** 2)

    total_pixels = h * w
    valid_count = np.sum(grad_mag > threshold)
    return float(valid_count / total_pixels)


def compute_structure_info(original: np.ndarray, processed: np.ndarray) -> float:
    """
    计算结构信息指标 S — 基于 SSIM 的结构分量
    """
    gray1 = np.mean(original.astype(np.float64)[:, :, :3], axis=2)
    gray2 = np.mean(processed.astype(np.float64)[:, :, :3], axis=2)

    C2 = (0.03 * 255) ** 2
    window_size = 11

    mu1 = uniform_filter(gray1, size=window_size)
    mu2 = uniform_filter(gray2, size=window_size)

    sigma1_sq = uniform_filter(gray1 * gray1, size=window_size) - mu1 * mu1
    sigma2_sq = uniform_filter(gray2 * gray2, size=window_size) - mu2 * mu2
    sigma12 = uniform_filter(gray1 * gray2, size=window_size) - mu1 * mu2

    sigma1 = np.sqrt(np.maximum(sigma1_sq, 0))
    sigma2 = np.sqrt(np.maximum(sigma2_sq, 0))

    structure_map = (sigma12 + C2 / 2) / (sigma1 * sigma2 + C2 / 2)
    return float(np.mean(structure_map))


def compute_evaluation(
    original: np.ndarray,
    processed: np.ndarray
) -> dict:
    """
    计算论文 5 项评价指标
    """
    sigma = compute_contrast_sigma(processed)
    d = compute_hue_fidelity(original, processed)
    I_valid = compute_valid_detail(processed)
    S = compute_structure_info(original, processed)

    # 综合指标
    q = S * I_valid * d * sigma / 10.0

    return {
        "sigma": round(sigma, 2),
        "d": round(d, 4),
        "I_valid": round(I_valid, 4),
        "S": round(S, 4),
        "q": round(q, 4),
    }
