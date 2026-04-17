"""
图像质量评估指标
"""

import numpy as np


def compute_psnr(image1: np.ndarray, image2: np.ndarray) -> float:
    """
    计算峰值信噪比 (PSNR)
    """
    mse = compute_mse(image1, image2)
    if mse == 0:
        return float('inf')
    return 10.0 * np.log10(255.0 ** 2 / mse)


def compute_mse(image1: np.ndarray, image2: np.ndarray) -> float:
    """
    计算均方误差 (MSE)
    """
    img1 = image1.astype(np.float64)
    img2 = image2.astype(np.float64)
    mse = np.mean((img1 - img2) ** 2)
    return float(mse)


def compute_ssim(
    image1: np.ndarray,
    image2: np.ndarray,
    window_size: int = 11,
    C1: float = 6.5025,
    C2: float = 58.5225
) -> float:
    """
    计算结构相似性指数 (SSIM)
    """
    img1 = image1.astype(np.float64)
    img2 = image2.astype(np.float64)

    # 如果是彩色图像，分别计算各通道 SSIM 再取平均
    if len(img1.shape) == 3:
        ssim_channels = []
        for c in range(img1.shape[2]):
            ssim_channels.append(
                _ssim_single_channel(img1[:, :, c], img2[:, :, c], window_size, C1, C2)
            )
        return float(np.mean(ssim_channels))
    else:
        return _ssim_single_channel(img1, img2, window_size, C1, C2)


def _ssim_single_channel(
    img1: np.ndarray,
    img2: np.ndarray,
    window_size: int,
    C1: float,
    C2: float
) -> float:
    """
    单通道 SSIM 计算（使用均匀滑动窗口）

    Args:
        img1, img2: 单通道图像 (H, W)，float64
        window_size: 窗口大小
        C1, C2: 稳定常数

    Returns:
        该通道的 SSIM 值
    """
    # 使用均匀窗口（简化计算）
    from scipy.ndimage import uniform_filter

    mu1 = uniform_filter(img1, size=window_size)
    mu2 = uniform_filter(img2, size=window_size)

    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = uniform_filter(img1 * img1, size=window_size) - mu1_sq
    sigma2_sq = uniform_filter(img2 * img2, size=window_size) - mu2_sq
    sigma12 = uniform_filter(img1 * img2, size=window_size) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))

    return float(np.mean(ssim_map))


def compute_metrics(
    original: np.ndarray,
    processed: np.ndarray
) -> dict:
    """
    计算全套质量评估指标
    """
    return {
        "psnr": compute_psnr(original, processed),
        "ssim": compute_ssim(original, processed),
        "mse": compute_mse(original, processed)
    }
