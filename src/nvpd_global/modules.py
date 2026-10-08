"""Short, one-function-per-module interface for the reproduction notebook."""
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
import numpy as np
from .config import Config
from .data import load_samples
from .representation import normal_distribution, align_facade_peak, smooth_azimuth
from .analysis import js_distance_matrix, average_hca
from .contributions import cluster_profiles
from .pipeline import Representations, export_results


@dataclass(frozen=True)
class Stage:
    """中文：每一步的结果对象，携带样本顺序、参数和输出路径。函数通过 replace 返回新对象，保留上一步；各阶段矩阵用 .raw/.aligned/.smoothed 访问。底层数组共享以节省内存，使用者应将其视为只读。

    English:
    A module's output, carrying arrays, settings and sample order forward.
    
    Each function returns a new Stage instead of overwriting its input. For
    example, raw.raw, aligned.aligned and smoothed.smoothed expose the actual
    N x 180 x 360 matrices. Arrays are shared, not copied, between stages.
    """
    samples: list
    config: Config
    output: Path
    display: bool
    make_plots: bool
    individual_images: bool
    name: str = "preprocessed"
    raw: np.ndarray | None = None
    aligned: np.ndarray | None = None
    smoothed: np.ndarray | None = None
    anchors: np.ndarray | None = None
    profiles: np.ndarray | None = None
    search_profiles: np.ndarray | None = None
    distance: np.ndarray | None = None
    hca: object = None
    cluster_profiles: dict | None = None


def _require(stage, name):
    if not isinstance(stage, Stage) or stage.name != name:
        raise ValueError(f"This module requires the '{name}' stage as input")


def _show(stage, function, *args):
    """Render inside a notebook only; batch use does not create preview plots."""
    if not stage.display:
        return
    try:
        from IPython import get_ipython
        from IPython.display import display
    except ImportError:
        return
    shell = get_ipython()
    if shell is None or not getattr(shell, "kernel", None):
        return
    from . import plotting
    import matplotlib.pyplot as plt
    figure = getattr(plotting, function)(*args)
    try:
        display(figure)
    finally:
        plt.close(figure)


def preprocess(input_dir, output_dir=None, *, input_mode="voxel_points",
               voxel_coefficient=0.009, normal_k=7, sample_table=None,
               display=True, make_plots=True, individual_images=True):
    """中文：加载 43 例点云并准备法向。默认 voxel_points 不再体素化但重新计算 k=7 法向；notebook 使用 prepared 直接读入已处理点云和对应法向。返回 Stage.samples，显示全部点云。输出文件统一在 save_results 写入，路径由启动模块自动确定。

    English:
    Load the 43-sample catalog and prepare oriented PCA normals.
    
    Default mode loads prevoxelized points: no repeated voxelization. obj and
    raw_points additionally voxelize using coefficient * original height.
    prepared loads matching, already oriented normals. A bundled paper catalog
    is used unless sample_table is supplied. The declared coefficient must match
    the input: 0.009 for paper reproduction, 0.025 for the public demonstration.
    
    Returns Stage with samples and Config; displays the all-sample cloud atlas.
    Output is written only by save_results, using a new/empty result directory.
    """
    config = Config(voxel_coefficient=voxel_coefficient, normal_k=normal_k)
    if sample_table is not None:
        catalog = Path(sample_table)
    elif (Path(input_dir) / "samples.csv").is_file():
        catalog = Path(input_dir) / "samples.csv"
    else:
        catalog = Path(__file__).with_name("hebei43.csv")
    output = Path(output_dir) if output_dir is not None else Path.cwd() / (
        "nvpd_results_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Choose a new or empty result directory")
    samples = load_samples(input_dir, input_mode, config, catalog)
    stage = Stage(samples, config, output, display, make_plots, individual_images)
    normal_action = "加载已有法向 / loaded normals" if input_mode == "prepared" else "计算PCA法向 / estimated normals"
    print(f"预处理 / Preprocessing: {len(samples)} samples, {sum(len(s.points) for s in samples):,} points; "
          f"{normal_action}; k={normal_k}; input coefficient={voxel_coefficient}H.")
    _show(stage, "point_cloud_atlas", samples)
    return stage


def compute_nvpd(data):
    """中文：输入预处理阶段对象。内部完成全部样本的球坐标映射、1° 分箱和概率归一化；返回新阶段对象，.raw 为 N×180×360 矩阵。自动显示全部样本原始 NVPD。

    English:
    Map normals, bin at 1 degree and normalize. Returns stage.raw; shows all samples.
    """
    _require(data, "preprocessed")
    raw = np.stack([normal_distribution(s.normals) for s in data.samples])
    stage = replace(data, name="nvpd", raw=raw)
    print(f"NVPD: {raw.shape}; each sample has unit total probability.")
    _show(stage, "nvpd_atlas", raw, data.samples, "Raw NVPDs — all samples", float(raw.max()))
    return stage


def align_nvpd(nvpd):
    """中文：输入原始 NVPD 阶段。内部批量完成 [80°,100°) 极角带的峰值搜索与整矩阵移动；返回 .aligned、.anchors 和诊断曲线。自动展示所有对齐矩阵和峰值曲线。

    English:
    Align facade peaks; returns .aligned/.anchors and shows atlas plus diagnostics.
    """
    _require(nvpd, "nvpd")
    alignment = [align_facade_peak(m, nvpd.config.facade_band, nvpd.config.peak_window) for m in nvpd.raw]
    stage = replace(nvpd, name="aligned", aligned=np.stack([a[0] for a in alignment]),
        anchors=np.array([a[1]["anchor_deg"] for a in alignment]),
        profiles=np.stack([a[1]["profile"] for a in alignment]),
        search_profiles=np.stack([a[1]["search_profile"] for a in alignment]))
    print(f"Alignment: polar band {stage.config.facade_band} degrees; peak anchors {stage.anchors.tolist()}.")
    _show(stage, "nvpd_atlas", stage.aligned, stage.samples, "Peak-aligned NVPDs — all samples", float(stage.raw.max()))
    diagnostics = Representations(stage.raw, stage.aligned, stage.aligned, stage.anchors,
                                  stage.profiles, stage.search_profiles)
    _show(stage, "peak_atlas", diagnostics, stage.samples)
    return stage


def smooth_nvpd(aligned):
    """中文：输入对齐阶段；批量做仅方位角 1×5 循环重叠均值。输出 .smoothed，尺寸不变；自动显示全部样本，颜色范围与前两阶段一致。

    English:
    Apply 1x5 circular azimuth averaging AFTER alignment. Returns .smoothed.
    """
    _require(aligned, "aligned")
    smoothed = np.stack([smooth_azimuth(m, aligned.config.smoothing_width) for m in aligned.aligned])
    stage = replace(aligned, name="smoothed", smoothed=smoothed)
    print(f"Smoothing: 1x{stage.config.smoothing_width}, stride 1; shape remains {smoothed.shape}.")
    _show(stage, "nvpd_atlas", smoothed, stage.samples, "Aligned then smoothed NVPDs — all samples", float(stage.raw.max()))
    return stage


def compute_distances(smoothed):
    """中文：输入平滑阶段。批量计算底数 2 的 √JSD，返回 .distance（N×N）；打印样本对数量与中位数并展示编号距离矩阵。

    English:
    Calculate all-pair sqrt(JSD_2). Returns .distance; displays the distance matrix.
    """
    _require(smoothed, "smoothed")
    distance = js_distance_matrix(smoothed.smoothed)
    stage = replace(smoothed, name="distances", distance=distance)
    pairs = distance[np.triu_indices(len(distance), 1)]
    print(f"Distance: {distance.shape}; {len(pairs)} pairs; median sqrt(JSD)={np.median(pairs):.8f}.")
    _show(stage, "distance_figure", distance, stage.samples)
    return stage


def cluster_hca(distances, *, manual_k=None):
    """中文：输入距离阶段，用平均链接建立树，并在有效 k=2…8 中按轮廓系数自动选簇。manual_k 可手动切分；默认无需设置。返回 .hca，其中含标签、树、分数和切线高度，展示树状图与轮廓曲线。

    English:
    Average linkage and silhouette-selected k=2..8; optional manual cut.
    
    Returns .hca including labels, linkage, silhouettes and selected cut height.
    Displays the tree and silhouette curve; tree colors use the selected k.
    """
    _require(distances, "distances")
    config = replace(distances.config, manual_k=manual_k)
    hca = average_hca(distances.distance, config.candidate_k, manual_k)
    stage = replace(distances, name="clusters", config=config, hca=hca)
    groups, counts = np.unique(hca.labels, return_counts=True)
    print(f"HCA: best k={hca.best_k}, selected k={hca.selected_k}; "
          f"mean silhouette={hca.silhouette.mean():.8f}; sizes={dict(zip(groups.tolist(), counts.tolist()))}.")
    _show(stage, "hca_figure", hca, stage.samples)
    _show(stage, "silhouette_figure", hca)
    return stage


def compare_clusters(clusters):
    """中文：输入聚类阶段。输出 .cluster_profiles，包含簇均值、簇内贡献、有/无符号簇间贡献及样本对数量。自动展示三类热图；使用无符号贡献统计大小，有符号图只表示概率差异方向。

    English:
    All-member means and all-pair difference maps; returns .cluster_profiles.
    
    Shows cluster means, within-cluster unsigned contributions and between-
    cluster signed contributions. Saved unsigned cross-cluster maps quantify
    magnitude; signed maps show direction and may cancel across pairs.
    """
    _require(clusters, "clusters")
    maps = cluster_profiles(clusters.smoothed, clusters.distance, clusters.hca.labels)
    stage = replace(clusters, name="compared", cluster_profiles=maps)
    print("Cluster comparison: all-member means and all within-/cross-cluster sample pairs.")
    _show(stage, "profile_figure", maps, "means")
    _show(stage, "profile_figure", maps, "within")
    _show(stage, "between_figure", maps)
    return stage


def save_results(comparison):
    """中文：输入簇比较阶段。保存全部矩阵、距离/分簇表、参数与哈希及 140 张主实验 PNG（43 例的三个阶段独立图共 129 张，加 11 张总览）。返回 result 字典，result["output"] 是结果目录，不覆盖先前运行。

    English:
    Export every numerical stage and complete figure set. Returns result dict.
    
    Individual images cover raw, aligned and smoothed NVPDs for every sample.
    Original point/normal arrays are not copied. Output order and input hashes
    are recorded alongside parameters and library versions.
    """
    _require(comparison, "compared")
    reps = Representations(comparison.raw, comparison.aligned, comparison.smoothed,
        comparison.anchors, comparison.profiles, comparison.search_profiles)
    output = export_results(comparison.samples, reps, comparison.distance, comparison.hca,
        comparison.cluster_profiles, comparison.output, comparison.config,
        make_plots=comparison.make_plots, individual_images=comparison.individual_images,
        save_point_arrays=False)
    print(f"Complete results saved to: {output.resolve()}")
    return {"samples": comparison.samples, "representations": reps, "distance": comparison.distance,
            "hca": comparison.hca, "cluster_profiles": comparison.cluster_profiles, "output": output}
