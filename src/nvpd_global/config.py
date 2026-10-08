"""Explicit parameters for the main experiment, with no parameter sweeps."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Config:
    """中文：论文主实验参数。voxel_coefficient 是体素边长/原模型高度 H；已体素化输入只记录该值，不再处理。normal_k 含查询点本身；facade_band 为左闭右开的极角范围（度）；峰值搜索与平滑窗口都是方位列数。manual_k=None 自动按轮廓系数选簇；块大小只控制临时内存，不改变邻域定义。

    English:
    Numerical settings; angles are degrees and H is the original z extent.
    
    voxel_coefficient is used only when voxelizing raw input. For previously
    voxelized input it records the declared input resolution, without applying
    voxelization a second time. normal_k includes the query point itself,
    matching the implementation used for the paper. manual_k=None selects the
    best valid average-linkage cut by mean silhouette, breaking ties toward
    fewer clusters. manual_k is an optional exploratory display override.
    """
    # 体素边长/H，无量纲 / Voxel side divided by original height, dimensionless.
    voxel_coefficient: float = 0.009
    # PCA 邻域含自身 / PCA neighborhood includes the query point.
    normal_k: int = 7
    # 极角左闭右开区间，单位为度 / Half-open polar band in degrees.
    facade_band: tuple[int, int] = (80, 100)
    # 仅用于找峰 / Only for finding the alignment peak.
    peak_window: int = 5
    # 对齐后仅平滑方位列，步长1 / Azimuth-only averaging after alignment, stride one.
    smoothing_width: int = 5
    # 选簇候选，不是预处理参数扫描 / Candidate tree cuts, not preprocessing sweeps.
    candidate_k: tuple[int, ...] = tuple(range(2, 9))
    # 默认自动选簇 / Automatic selection by default.
    manual_k: int | None = None
    # 临时内存控制 / Temporary-memory limit, not a geometric parameter.
    normal_block_size: int = 2000

    def __post_init__(self):
        if not 0 < self.voxel_coefficient < 1:
            raise ValueError("voxel_coefficient must lie between zero and one")
        if self.normal_k < 3 or self.normal_block_size < 1:
            raise ValueError("normal_k >= 3 and normal_block_size >= 1 are required")
        lo, hi = self.facade_band
        if not (isinstance(lo, int) and isinstance(hi, int) and 0 <= lo < hi <= 180):
            raise ValueError("facade_band must have integer bounds within [0, 180]")
        for width in (self.peak_window, self.smoothing_width):
            if not isinstance(width, int) or not 1 <= width <= 359 or width % 2 != 1:
                raise ValueError("Circular window widths must be positive odd integers <= 359")
        if not self.candidate_k or any(not isinstance(k, int) or k < 2 for k in self.candidate_k):
            raise ValueError("candidate_k must contain integer cluster counts >= 2")
        if self.manual_k is not None and self.manual_k not in self.candidate_k:
            raise ValueError("manual_k must belong to candidate_k")

    def as_dict(self):
        return asdict(self)
