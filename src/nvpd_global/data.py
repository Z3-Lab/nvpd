"""Portable input discovery. All computation follows one stable sample order."""
from dataclasses import dataclass, field
from pathlib import Path
import csv
import hashlib
import numpy as np
from .config import Config
from .preprocessing import (load_points, face_referenced_vertices, voxel_downsample,
                            estimate_normals, xyz_array)


@dataclass
class Sample:
    name: str
    sample_id: str
    points: np.ndarray
    normals: np.ndarray
    metadata: dict = field(default_factory=dict)


def bundled_data_dir():
    """中文：自动返回包内 43 例 0.009H 点云及 k=7 法向目录，解压源码或安装包后均可使用，无需手动填写路径。

    English:
    Return the installed package's 43-sample 0.009H points/normal directory.
    """
    directory = Path(__file__).with_name("datasets") / "hebei43_0_009H"
    if not (directory / "samples.csv").is_file():
        raise FileNotFoundError("Bundled dataset is missing; reinstall the complete package")
    return directory


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _discover(directory, mode):
    suffixes = (".obj",) if mode == "obj" else (".npy", ".xyz", ".txt", ".ply")
    files = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in suffixes or path.stem.endswith("_normals"):
            continue
        name = path.stem.removesuffix("_points")
        # Prefer NPY when a release provides several encodings of the same cloud.
        if name not in files or path.suffix.lower() == ".npy":
            files[name] = path
    if not files:
        raise ValueError(f"No {mode} inputs found in the selected directory")
    return files


def load_samples(directory, mode="voxel_points", config=None, sample_table=None):
    """中文：根据样本表按名称排序加载全部输入；显示编号 sample_id 不是数组索引。prepared 模式直接复用对应法向，voxel_points 模式重新求法向，obj/raw_points 额外体素化。可在 CSV 中声明体素系数/邻域并核对；所有文件名按数据目录解析，保存哈希用于追溯。

    English:
    Load one dataset with mode obj, raw_points, voxel_points or prepared.
    
    obj/raw_points apply proportional voxelization. voxel_points skips it and
    estimates normals. prepared skips both, loading <sample>_points.npy and
    <sample>_normals.npy in matching order; supplied normals must already follow
        the paper's orientation convention. Loading leaves the input files unchanged.
    
    Optional CSV has sample and sample_id columns. Optional points_file and
    normals_file columns are resolved relative to directory. Optional
    voxel_coefficient/normal_k fields are checked against declared config. The
    requested sample set must be complete. Processing order is alphabetical by
    identifier; sample_id is only a display ID, never an array index.
    """
    config = config or Config()
    if mode not in ("obj", "raw_points", "voxel_points", "prepared"):
        raise ValueError("mode must be obj, raw_points, voxel_points or prepared")
    directory = Path(directory).expanduser().resolve()
    if sample_table is None:
        files = _discover(directory, mode)
        rows = [{"sample": name, "sample_id": str(i + 1)} for i, name in enumerate(sorted(files))]
    else:
        with Path(sample_table).open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        if not rows or any(not row.get("sample") for row in rows):
            raise ValueError("Sample CSV must contain a nonempty sample column")
        files = _discover(directory, mode) if any(not r.get("points_file") for r in rows) else {}
    rows = sorted(rows, key=lambda r: r["sample"])
    if len({r["sample"] for r in rows}) != len(rows):
        raise ValueError("Duplicate sample identifiers")
    samples = []
    for i, row in enumerate(rows):
        name = row["sample"]
        path = directory / row["points_file"] if row.get("points_file") else files.get(name)
        if path is None or not path.is_file():
            raise FileNotFoundError(f"Missing requested sample: {name}")
        if mode in ("voxel_points", "prepared") and row.get("voxel_coefficient"):
            if not np.isclose(float(row["voxel_coefficient"]), config.voxel_coefficient):
                raise ValueError(f"Input voxel coefficient disagrees with config: {name}")
        points = face_referenced_vertices(path) if mode == "obj" else load_points(path)
        meta = {"input_mode": mode, "input_file": path.name, "input_sha256": sha256_file(path),
                "voxelization_applied": False, "input_resolution_declared": config.voxel_coefficient}
        if mode in ("obj", "raw_points"):
            points, info = voxel_downsample(points, config.voxel_coefficient)
            meta.update(info)
        if mode == "prepared":
            normal_path = directory / (row.get("normals_file") or f"{name}_normals.npy")
            normals = xyz_array(np.load(normal_path, allow_pickle=False), "normals")
            if normals.shape != points.shape or np.any(np.linalg.norm(normals, axis=1) == 0):
                raise ValueError(f"Invalid matching normals: {name}")
            if row.get("normal_k") and int(row["normal_k"]) != config.normal_k:
                raise ValueError(f"Input normal_k disagrees with config: {name}")
            meta.update(normals_supplied=True, normals_file=normal_path.name,
                        normals_sha256=sha256_file(normal_path))
        else:
            normals = estimate_normals(points, config.normal_k, config.normal_block_size)
            meta["normals_supplied"] = False
        meta.update(point_count=len(points), point_z_span=float(np.ptp(points[:, 2])))
        samples.append(Sample(name, str(row.get("sample_id") or i + 1), points, normals, meta))
    if len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("Display sample IDs must be unique")
    return samples
