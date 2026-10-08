"""Primary-experiment PNG figures. Display transforms never change data."""
from pathlib import Path
from itertools import combinations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm, FuncNorm, LinearSegmentedColormap
from scipy.cluster.hierarchy import dendrogram

COLORS = ["#D55E00", "#009E73", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#882255", "#44AA99"]
SIGNED = LinearSegmentedColormap.from_list("nvpd_signed", ["#1565C0", "#FFFFFF", "#D62828"], N=257)


def save_figure(fig, path):
    """中文：以 200 dpi 输出 PNG 并关闭 figure，避免批量保存时占用过多绘图内存。

    English:
    Save a readable 200-dpi PNG and close its Matplotlib figure.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _heat(ax, matrix, norm, cmap="magma_r", title=""):
    img = ax.imshow(matrix, origin="upper", extent=(0, 360, 180, 0),
                    aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
    ax.set(xticks=[0, 90, 180, 270, 360], yticks=[0, 45, 90, 135, 180],
           xlabel="Azimuth (degrees)", ylabel="Polar angle (degrees)", title=title)
    ax.tick_params(labelsize=7)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    ax.title.set_size(9)
    return img


def _grid(ax):
    ax.set_facecolor("#F0F0F0")
    ax.set_axisbelow(True)
    ax.grid(True, axis="both", color="white", linewidth=0.9)
    for spine in ax.spines.values():
        spine.set_linewidth(0.6)


def point_cloud_atlas(samples, max_display_points=8000):
    """中文：显示全部样本。仅显示时用确定性索引最多抽取 8000 点，并平移/按高度缩放以便比较；分析输入数组不改变。PCA 与 NVPD 使用全部输入点。

    English:
    All inputs in sample-ID order. Deterministic display subsampling only.
    
    Coordinates are translated and divided by each cloud's z-span for display;
    the numerical input arrays are unchanged. PCA still uses every input point.
    """
    columns = 5
    rows = int(np.ceil(len(samples) / columns))
    fig = plt.figure(figsize=(14, 3.2 * rows), constrained_layout=True)
    for i, sample in enumerate(samples):
        ax = fig.add_subplot(rows, columns, i + 1, projection="3d")
        points = sample.points
        indices = np.linspace(0, len(points) - 1, min(len(points), max_display_points), dtype=int)
        scale = float(np.ptp(points[:, 2])) or float(np.max(np.ptp(points, axis=0))) or 1
        cloud = (points[indices] - points.mean(axis=0)) / scale
        ax.scatter(*cloud.T, s=0.3, c=cloud[:, 2], cmap="Greys", rasterized=True)
        ax.view_init(elev=15, azim=-65)
        ax.set_proj_type("ortho")
        span = max(np.ptp(cloud, axis=0)) / 2
        center = (cloud.min(axis=0) + cloud.max(axis=0)) / 2
        ax.set(xlim=(center[0]-span, center[0]+span), ylim=(center[1]-span, center[1]+span),
               zlim=(center[2]-span, center[2]+span))
        ax.set_box_aspect((1, 1, 1))
        ax.set_axis_off()
        ax.set_title(f"{sample.sample_id}: {sample.name}\n{len(points):,} points", fontsize=7)
    fig.suptitle("Input voxel clouds — display subsampling only", fontsize=13)
    return fig


def nvpd_atlas(matrices, samples, title, vmax=None):
    """中文：全部样本共用一个色标。gamma=0.3 为显示增强；原始、对齐、平滑阶段使用相同 vmax，保存的概率不改变。

    English:
    Show every sample; a shared gamma=0.3 probability color scale.
    """
    columns = 5
    rows = int(np.ceil(len(samples) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(15, 2.3 * rows), squeeze=False,
                             constrained_layout=True)
    norm = PowerNorm(0.3, vmin=0, vmax=vmax or float(np.max(matrices)))
    for i, ax in enumerate(axes.flat):
        if i >= len(samples):
            ax.set_visible(False)
            continue
        img = _heat(ax, matrices[i], norm, title=f"Sample {samples[i].sample_id}")
    fig.colorbar(img, ax=list(axes.flat), shrink=0.8, label="Probability per 1-degree bin")
    fig.suptitle(title, fontsize=13)
    return fig


def peak_atlas(representations, samples):
    """中文：显示原始方位概率曲线、只用于峰搜索的五列均值曲线及对齐前的选中峰角度，不表示后续 NVPD 平滑结果。

    English:
    Raw and five-column peak-search profiles; selected peak before shifting.
    """
    rows = int(np.ceil(len(samples) / 5))
    fig, axes = plt.subplots(rows, 5, figsize=(15, 2.1 * rows), squeeze=False, constrained_layout=True)
    for i, ax in enumerate(axes.flat):
        if i >= len(samples):
            ax.set_visible(False)
            continue
        _grid(ax)
        ax.plot(representations.profiles[i], color="#777777", lw=0.8, label="Raw profile")
        ax.plot(representations.search_profiles[i], color="#0072B2", lw=1, label="Peak-search average")
        ax.axvline(representations.anchors[i], color="#D55E00", ls="--", lw=1)
        ax.set(xlim=(0, 360), title=f"Sample {samples[i].sample_id}: peak {representations.anchors[i]} degrees",
               xlabel="Azimuth (degrees)", ylabel="Polar-band probability")
        ax.tick_params(labelsize=6)
        ax.title.set_size(8)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
    axes.flat[0].legend(fontsize=6)
    return fig


def distance_figure(distance, samples):
    fig, ax = plt.subplots(figsize=(11, 10), constrained_layout=True)
    image = ax.imshow(distance, vmin=0, vmax=1, cmap="viridis", interpolation="nearest")
    positions = np.arange(len(samples))
    labels = [s.sample_id for s in samples]
    ax.set(xticks=positions, yticks=positions, xticklabels=labels, yticklabels=labels,
           xlabel="Sample ID", ylabel="Sample ID", title="Pairwise Jensen–Shannon distance (base 2)")
    ax.tick_params(labelsize=6)
    fig.colorbar(image, ax=ax, label="Square root of JSD (0–1)")
    return fig


def hca_figure(hca, samples):
    """中文：叶节点使用样本编号，分支颜色按选定簇成员确定，水平虚线按相同 selected_k 的切分高度绘制。

    English:
    Numbered leaves; branch colors and cut line use the SELECTED k.
    """
    n = len(samples)
    members = {i: {i} for i in range(n)}
    for i, row in enumerate(hca.tree):
        members[n+i] = members[int(row[0])] | members[int(row[1])]
    def color(node):
        groups = {int(hca.labels[i]) for i in members[int(node)]}
        return COLORS[(next(iter(groups))-1) % len(COLORS)] if len(groups) == 1 else "#646464"
    fig, ax = plt.subplots(figsize=(15, 4.7), constrained_layout=True)
    _grid(ax)
    dendrogram(hca.tree, labels=[str(s.sample_id) for s in samples], ax=ax,
               leaf_rotation=0, leaf_font_size=8, link_color_func=color)
    ax.axhline(hca.cut_height, color="#994400", ls="--", lw=1,
               label=f"Selected k={hca.selected_k}; cut={hca.cut_height:.4f}")
    ax.set(xlabel="Sample ID (see samples.csv)", ylabel="Average-linkage distance",
           title="Global hierarchical clustering")
    ax.legend(loc="upper left", fontsize=9)
    return fig


def silhouette_figure(hca):
    fig, ax = plt.subplots(figsize=(6.5, 4), constrained_layout=True)
    _grid(ax)
    keys = sorted(hca.scores)
    ax.plot(keys, [hca.scores[k] for k in keys], "o-", color="#0072B2")
    ax.scatter([hca.selected_k], [hca.scores[hca.selected_k]], color="#D55E00", s=65,
               label=f"Selected k={hca.selected_k} (best k={hca.best_k})", zorder=3)
    ax.set(xticks=keys, xlabel="Number of clusters", ylabel="Mean silhouette coefficient",
           title="Cluster-number selection — average linkage")
    ax.legend(fontsize=8)
    return fig


def profile_figure(profiles, kind="means"):
    """中文：显示簇均值或簇内无符号距离贡献图，每个图内共用色标；不同含义的图不混用数值尺度。

    English:
    All-member means or mean within-cluster distance-contribution maps.
    """
    if kind not in {"means", "within"}:
        raise ValueError("kind must be means or within")
    groups = sorted(profiles[kind])
    matrices = [profiles[kind][g] if kind == "means" else profiles[kind][g]["map"] for g in groups]
    norm = PowerNorm(0.3, vmin=0, vmax=max(float(np.max(m)) for m in matrices) or 1)
    columns = min(3, len(groups))
    rows = int(np.ceil(len(groups) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(5*columns, 3.2*rows), squeeze=False,
                             constrained_layout=True)
    for i, ax in enumerate(axes.flat):
        if i >= len(groups):
            ax.set_visible(False)
            continue
        title = f"Cluster {groups[i]}"
        if kind == "within":
            count = profiles[kind][groups[i]]["pair_count"]
            title += f" — {count} within-cluster pairs"
        img = _heat(ax, matrices[i], norm, title=title)
    label = "Mean bin probability" if kind == "means" else "Mean bin contribution to distance"
    fig.colorbar(img, ax=list(axes.flat), shrink=0.8, label=label)
    return fig


def between_figure(profiles):
    """中文：显示全部交叉样本对平均的有符号贡献。红色表示前簇概率较多，蓝色表示后簇较多；白色也可能由抵消产生。共用对称蓝白红色标，非线性映射只用于显示。

    English:
    Signed contributions averaged over ALL cross-cluster pairs.
    
    Red: greater bin probability in the first cluster; blue: in the second.
    Shared signed-power display scale. White can also reflect cancellation;
    consult saved unsigned maps to quantify total differences.
    """
    pairs = sorted(profiles["between"])
    limit = max(float(np.max(np.abs(profiles["between"][p]["signed"]))) for p in pairs) or 1
    forward = lambda x: np.sign(x) * np.abs(x)**0.3
    inverse = lambda x: np.sign(x) * np.abs(x)**(1/0.3)
    norm = FuncNorm((forward, inverse), vmin=-limit, vmax=limit)
    columns = min(3, len(pairs))
    rows = int(np.ceil(len(pairs) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(5*columns, 3.3*rows), squeeze=False,
                             constrained_layout=True)
    for i, ax in enumerate(axes.flat):
        if i >= len(pairs):
            ax.set_visible(False)
            continue
        left, right = pairs[i]
        item = profiles["between"][pairs[i]]
        img = _heat(ax, item["signed"], norm, cmap=SIGNED,
                    title=f"Cluster {left} (red) vs {right} (blue)\n{item['pair_count']} cross-cluster pairs")
    fig.colorbar(img, ax=list(axes.flat), shrink=0.8, label="Mean signed bin contribution")
    return fig


def plot_all(samples, representations, distance, hca, profiles, output, individual_images=True):
    """中文：统一保存 11 张总览/分析图及每个样本三个阶段的独立 NVPD 图；图像之外的数值由 export_results 保存。

    English:
    Save all-sample stage atlases, primary HCA and interpretation graphics.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_figure(point_cloud_atlas(samples), output / "01_input_clouds.png")
    vmax = float(np.max(representations.raw))
    for number, key in enumerate(("raw", "aligned", "smoothed"), 2):
        save_figure(nvpd_atlas(getattr(representations, key), samples, f"{key.capitalize()} NVPDs", vmax),
                    output / f"{number:02d}_{key}_nvpd.png")
    save_figure(peak_atlas(representations, samples), output / "05_peak_alignment.png")
    save_figure(distance_figure(distance, samples), output / "06_distance_matrix.png")
    save_figure(hca_figure(hca, samples), output / "07_hca.png")
    save_figure(silhouette_figure(hca), output / "08_silhouette.png")
    save_figure(profile_figure(profiles, "means"), output / "09_cluster_means.png")
    save_figure(profile_figure(profiles, "within"), output / "10_within_cluster_differences.png")
    save_figure(between_figure(profiles), output / "11_between_cluster_differences.png")
    if individual_images:
        norm = PowerNorm(0.3, vmin=0, vmax=vmax)
        for i, sample in enumerate(samples):
            for stage in ("raw", "aligned", "smoothed"):
                fig, ax = plt.subplots(figsize=(6, 3.4), constrained_layout=True)
                img = _heat(ax, getattr(representations, stage)[i], norm,
                            title=f"Sample {sample.sample_id}: {sample.name} — {stage}")
                fig.colorbar(img, ax=ax, label="Bin probability")
                save_figure(fig, output / "samples" / f"{sample.sample_id}_{sample.name}_{stage}.png")
