"""One-degree NVPDs, facade-peak alignment, then azimuthal smoothing."""
import numpy as np
from scipy.ndimage import uniform_filter
from .preprocessing import xyz_array


def probability_matrix(matrix):
    """中文：检查 180×360 概率矩阵及单位总质量，保留原始数值不再缩放，避免额外浮点运算改变竞争峰的并列关系。

    English:
    Validate a unit-mass 180 x 360 NVPD without rescaling its entries.
    
    Keeping the original histogram values preserves the reference peak-search
    arithmetic, including its first-maximum rule for competing facade peaks.
    """
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.shape != (180, 360) or not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError("Expected a finite nonnegative 180 x 360 NVPD")
    mass = matrix.sum()
    if not np.isclose(mass, 1, rtol=0, atol=1e-12):
        raise ValueError("NVPD must have unit total mass")
    return matrix


def spherical_angles(normals):
    """中文：输入 N×3 非零法向，内部单位化；极角 θ 是与 +z 的夹角 [0°,180°]，方位角 φ 从 +x 朝 +y 计量并映射到 [0°,360°)。输出两个长度 N 的角度数组。

    English:
    Return theta from +z in [0,180] and azimuth phi from +x in [0,360), degrees.
    """
    normals = xyz_array(normals, "normals")
    length = np.linalg.norm(normals, axis=1)
    if np.any(length == 0):
        raise ValueError("Normals must not contain zero vectors")
    unit = normals / length[:, None]
    theta = np.degrees(np.arccos(np.clip(unit[:, 2], -1, 1)))
    phi = np.degrees(np.arctan2(unit[:, 1], unit[:, 0])) % 360
    return theta, phi


def normal_distribution(normals):
    """中文：每个法向投一票，以 1° 左闭右开角格分箱，再除以全部法向数。行是极角、列是方位角；θ=180° 放入最后一行。输出 180×360、总和为 1，表示每角格概率，不是单位球面面积密度。

    English:
    Count one vote per normal in one-degree bins, then divide by all votes.
    
    Rows represent [theta,theta+1), columns [phi,phi+1); theta=180 is clamped
    into the last row. This is directional probability, not equal-area spherical
    density. Output has shape (180,360), is nonnegative and sums to one.
    """
    theta, phi = spherical_angles(normals)
    row = np.minimum(np.floor(theta).astype(int), 179)
    col = np.floor(phi).astype(int)
    histogram = np.zeros((180, 360), dtype=np.float64)
    # 先计数，再除以总数；每个法向权重相同 / Equal normal votes, then total-count normalization.
    np.add.at(histogram, (row, col), 1)
    return histogram / histogram.sum()


def align_facade_peak(matrix, band=(80, 100), peak_window=5):
    """中文：输入未平滑 NVPD。累加极角 [80°,100°) 的各方位列，五列循环均值仅用于寻找最大峰，首次最大值处理并列。整张原矩阵沿列移动 -anchor；返回对齐矩阵与原始角度锚点/峰值诊断。峰值共同参考不等于物理立面严格对齐。

    English:
    Align an UNSMOOTHED NVPD by circularly shifting its facade-normal peak.
    
    Sum rows [band[0],band[1]); use peak_window-column circular averaging ONLY
    for peak search. The first maximum (numpy.argmax) breaks ties. Roll the entire
    original matrix by minus the peak column. Returns (aligned, diagnostics),
    including the original profile, peak-search profile and integer anchor.
    Peak alignment establishes a directional reference, not exact physical
    correspondence of architectural facades.
    """
    matrix = probability_matrix(matrix)
    lo, hi = band
    if not 0 <= lo < hi <= 180 or peak_window < 1 or peak_window % 2 != 1:
        raise ValueError("Invalid facade band or peak-search window")
    # 行索引80:100代表[80°,100°)，不含100° / Half-open polar interval, upper bound excluded.
    profile = matrix[lo:hi].sum(axis=0)
    radius = peak_window // 2
    search = sum(np.roll(profile, shift) for shift in range(-radius, radius + 1)) / peak_window
    # 并列峰选首次最大值，保持原实验的浮点运算顺序 / First maximum; preserve reference arithmetic.
    anchor = int(np.argmax(search))
    return np.roll(matrix, -anchor, axis=1), {"anchor_deg": anchor,
        "profile": profile, "search_profile": search, "facade_band_mass": float(profile.sum())}


def smooth_azimuth(matrix, width=5):
    """中文：输入已经峰值对齐的矩阵；1×5 窗口覆盖方位偏移 -2,-1,0,1,2，以步长 1 循环重叠求均值，不处理极角、不缩小矩阵。剔除负的浮点尾差并归一化，输出仍为 180×360。

    English:
    Circular overlapping 1 x width average, stride one; preserve all polar rows.
    
    Input must already be aligned for the paper's pipeline. A five-column window
    averages offsets -2,-1,0,1,2. The shape remains 180 x 360. Clip numerical
    roundoff below zero and explicitly normalize mass before distance calculation.
    """
    matrix = probability_matrix(matrix)
    if not isinstance(width, int) or not 1 <= width <= 359 or width % 2 != 1:
        raise ValueError("width must be a positive odd integer <= 359")
    # wrap使0°与359°相邻；极角窗仅1行 / Azimuth wraps across the seam; polar window is one row.
    smoothed = uniform_filter(matrix, size=(1, width), mode=("reflect", "wrap"), origin=0)
    smoothed = np.maximum(smoothed, 0)
    return smoothed / smoothed.sum()
