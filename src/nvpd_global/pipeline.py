"""Stepwise primary analysis and reproducible numerical/figure exports."""
from dataclasses import dataclass
from pathlib import Path
import csv
import json
import platform
from importlib.metadata import version, PackageNotFoundError
import numpy as np
from .config import Config
from .representation import normal_distribution, align_facade_peak, smooth_azimuth
from .analysis import js_distance_matrix, average_hca
from .contributions import cluster_profiles


@dataclass
class Representations:
    raw: np.ndarray
    aligned: np.ndarray
    smoothed: np.ndarray
    anchors: np.ndarray
    profiles: np.ndarray
    search_profiles: np.ndarray


def build_representations(samples, config=None):
    """中文：批量建立分箱、对齐、平滑三个 N×180×360 阶段，顺序固定为先对齐再平滑；同时返回每例峰值角度及诊断曲线，不做逐样本选参。

    English:
    Return all three N x 180 x 360 stages and peak-search diagnostics.
    
    Calling the low-level functions separately is equally supported. Align first,
    smooth second. No sample-specific parameter fitting or pairwise rotation
    optimization is performed in this primary pipeline.
    """
    config = config or Config()
    raw = np.stack([normal_distribution(s.normals) for s in samples])
    aligned, diagnostics = zip(*(align_facade_peak(m, config.facade_band, config.peak_window) for m in raw))
    aligned = np.stack(aligned)
    return Representations(raw, aligned, np.stack([smooth_azimuth(m, config.smoothing_width) for m in aligned]),
        np.array([d["anchor_deg"] for d in diagnostics]), np.stack([d["profile"] for d in diagnostics]),
        np.stack([d["search_profile"] for d in diagnostics]))


def _csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def export_results(samples, representations, distance, hca, profiles, output, config=None,
                   make_plots=True, individual_images=True, save_point_arrays=False):
    """中文：将完整数值阶段、样本顺序、输入哈希、依赖版本、树结构和簇统计输出为 CSV/JSON/NPY/NPZ，可选输出 PNG。使用新的或空目录，防止旧结果混入；输入点云/法向默认不再复制。

    English:
    Export primary numerical results, provenance and optional PNG graphics.
    
    Uses a fresh output directory to avoid mixing different runs. Point/normal
    arrays are not exported by default; enabling them may export restricted data.
    Bundled reproduction inputs are distributed with the package; run outputs
    are saved separately.
    Returns the output Path; all matrices use the order in samples.csv.
    """
    config = config or Config()
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Choose a new or empty output directory to keep each run coherent")
    output.mkdir(parents=True, exist_ok=True)
    names = [s.name for s in samples]
    _csv(output / "samples.csv", ["sample_id", "sample", "point_count", "point_z_span", "anchor_deg",
         "cluster", "silhouette", "input_mode", "declared_voxel_coefficient"],
         [[s.sample_id, s.name, len(s.points), s.metadata.get("point_z_span"), int(representations.anchors[i]),
           int(hca.labels[i]), float(hca.silhouette[i]), s.metadata.get("input_mode"), config.voxel_coefficient]
          for i, s in enumerate(samples)])
    _csv(output / "sqrt_jsd_matrix.csv", ["sample", *names], [[name, *distance[i]] for i, name in enumerate(names)])
    _csv(output / "silhouette_by_k.csv", ["k", "mean_silhouette", "is_best", "is_selected"],
         [[k, score, k == hca.best_k, k == hca.selected_k] for k, score in sorted(hca.scores.items())])
    _csv(output / "linkage.csv", ["left_node", "right_node", "height", "sample_count"], hca.tree)
    cluster_records = []
    for group in sorted(profiles["means"]):
        indices = np.flatnonzero(hca.labels == group)
        medoid = indices[np.argmin(distance[np.ix_(indices, indices)].mean(axis=1))]
        cluster_records.append({"cluster": group, "size": len(indices), "medoid": names[medoid],
                                "members": [names[i] for i in indices],
                                "within_pair_count": profiles["within"][group]["pair_count"],
                                "mean_within_distance": float(profiles["within"][group]["map"].sum())})
    arrays = output / "arrays"
    arrays.mkdir()
    for key in ("raw", "aligned", "smoothed", "anchors", "profiles", "search_profiles"):
        np.save(arrays / f"{key}.npy", getattr(representations, key))
    np.save(arrays / "distance.npy", distance)
    np.save(arrays / "labels.npy", hca.labels)
    map_data = {f"cluster_{g}_mean": m for g, m in profiles["means"].items()}
    map_data.update({f"cluster_{g}_within": v["map"] for g, v in profiles["within"].items()})
    pair_records = []
    for (left, right), item in profiles["between"].items():
        map_data[f"clusters_{left}_{right}_signed"] = item["signed"]
        map_data[f"clusters_{left}_{right}_unsigned"] = item["unsigned"]
        pair_records.append({"left": left, "right": right, "pair_count": item["pair_count"],
            "mean_distance": item["mean_distance"],
            "facade_band_unsigned_share": float(item["unsigned"][80:100].sum() / item["mean_distance"])
                if item["mean_distance"] > 0 else None})
    np.savez_compressed(arrays / "cluster_profiles.npz", **map_data)
    if save_point_arrays:
        point_dir = output / "point_arrays"
        point_dir.mkdir()
        for s in samples:
            np.save(point_dir / f"{s.name}_points.npy", s.points)
            np.save(point_dir / f"{s.name}_normals.npy", s.normals)
    versions = {"python": platform.python_version()}
    for package in ("numpy", "scipy", "matplotlib", "open3d", "nvpd-global"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            pass
    # 中文：直接从源码运行也记录实际代码版本，而非误用其他安装包的元数据。
    # English: record this source release even without installing the project.
    from . import __version__
    versions["nvpd-global"] = __version__
    summary = {"sample_count": len(samples), "sample_order": names, "parameters": config.as_dict(),
        "algorithm": {"matrix_shape": [180, 360], "distance": "sqrt(JSD), base 2", "linkage": "average",
            "order": ["PCA normals", "centroid orientation", "angular binning", "peak alignment", "azimuthal smoothing"]},
        "best_k": hca.best_k, "selected_k": hca.selected_k, "manual_override": config.manual_k is not None,
        "selected_mean_silhouette": float(hca.silhouette.mean()), "cut_height": hca.cut_height,
        "cophenetic_correlation": hca.cophenetic_correlation, "clusters": cluster_records,
        "between_cluster_comparisons": pair_records, "versions": versions,
        "input_provenance": {s.name: s.metadata for s in samples},
        "display": {"probability_colormap": "magma_r", "power_gamma": 0.3,
                    "signed_colormap": "blue-white-red", "signed_power_gamma": 0.3}}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if make_plots:
        from .plotting import plot_all
        plot_all(samples, representations, distance, hca, profiles, output / "figures", individual_images)
    return output


def run_global(samples, output, config=None, **export_options):
    """中文：供命令行/程序批量使用的低层组合入口；notebook 用独立模块展示流程。返回各阶段结果及输出目录。

    English:
    Run only the global primary experiment; return all intermediate results.
    """
    config = config or Config()
    if len({s.name for s in samples}) != len(samples):
        raise ValueError("Sample identifiers must be unique")
    representations = build_representations(samples, config)
    distance = js_distance_matrix(representations.smoothed)
    hca = average_hca(distance, config.candidate_k, config.manual_k)
    profiles = cluster_profiles(representations.smoothed, distance, hca.labels)
    path = export_results(samples, representations, distance, hca, profiles, output, config, **export_options)
    return {"samples": samples, "representations": representations, "distance": distance,
            "hca": hca, "cluster_profiles": profiles, "output": path}
