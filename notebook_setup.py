"""Notebook startup using only the Python standard library.

中文：自动准备当前 notebook 内核、包内代码、数据与输出路径。
English: prepare the current kernel, local source, bundled inputs and outputs.
This file can be loaded before NumPy, SciPy or Matplotlib has been installed.
"""
from datetime import datetime
from importlib import import_module, invalidate_caches, metadata
from pathlib import Path
import csv
import hashlib
import json
import os
import re
import subprocess
import sys


# 中文：仅安装主实验需要的三项依赖；现有兼容版本直接复用。
# English: install only the three core dependencies when missing/incompatible.
# No package installation, Open3D, GPU, path editing or sample selection is needed.
CORE_REQUIREMENTS = {
    "numpy": ((1, 24), 3, "numpy>=1.24,<3"),
    "scipy": ((1, 10), 2, "scipy>=1.10,<2"),
    "matplotlib": ((3, 7), 4, "matplotlib>=3.7,<4"),
}


def _compatible(version, minimum, upper_major):
    match = re.match(r"^(\d+)\.(\d+)", version)
    return bool(match and tuple(map(int, match.groups())) >= minimum
                and int(match.group(1)) < upper_major)


def _prepare_dependencies():
    """中文：在当前内核安装缺少的库。English: install into this kernel's Python."""
    missing = []
    for name, (minimum, upper_major, requirement) in CORE_REQUIREMENTS.items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = ""
        if not _compatible(installed, minimum, upper_major):
            missing.append(requirement)
    if missing:
        print("自动安装缺少的依赖 / Automatically installing dependencies:", ", ".join(missing), flush=True)
        # 中文：sys.executable 确保依赖装进当前 notebook 内核，避免装到另一套 Python。
        # English: use the active kernel executable rather than an unrelated 'pip'.
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *missing],
                           check=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError("自动安装未完成：首次缺少依赖时需要联网且当前 Python 环境可写。"
                               " / Automatic dependency installation failed: first use requires internet "
                               "and a writable Python environment when libraries are missing.") from error
        invalidate_caches()
    versions = {}
    for name, (minimum, upper_major, _) in CORE_REQUIREMENTS.items():
        module = import_module(name)
        versions[name] = module.__version__
        if not _compatible(module.__version__, minimum, upper_major):
            raise RuntimeError(f"{name} 已在内核中加载了不兼容版本；请使用新的 Python 3.10+ 内核。"
                               " / An incompatible version was already loaded; use a fresh Python 3.10+ kernel.")
    return versions


def _verify_inputs(directory):
    """中文：核对所有点云和法向的完整性。English: verify all 86 input hashes."""
    with (directory / "samples.csv").open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    if len(records) != 43 or len({row["sample"] for row in records}) != 43:
        raise ValueError("包内应包含 43 个唯一样本 / Expected 43 unique bundled samples")
    for row in records:
        if float(row["voxel_coefficient"]) != 0.009 or int(row["normal_k"]) != 7:
            raise ValueError("包内参数应为 0.009H、k=7 / Expected 0.009H and k=7")
        for kind in ("points", "normals"):
            path = directory / row[f"{kind}_file"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != row[f"{kind}_sha256"]:
                raise ValueError(f"数据文件损坏 / Data integrity check failed: {path.name}")
    return len(records)


def prepare_notebook(project_root=None):
    """Prepare the downloaded notebook with no user-supplied configuration.

    中文：自动定位源代码 → 检查/安装依赖 → 验证 43 例数据 → 建立输出路径。
    English: locate source, provision dependencies, verify inputs, select output.
    Returns a dictionary of Paths, dependency versions and fixed paper settings.
    Each Run All creates a new result directory; previous runs are preserved.
    """
    if sys.version_info < (3, 10):
        raise RuntimeError("需要 Python 3.10 或以上 / Python 3.10 or later is required")
    root = Path(project_root or Path(__file__).parent).resolve()
    source = root / "src"
    if not (source / "nvpd_global" / "__init__.py").is_file():
        raise FileNotFoundError("请保留完整的解压目录 / Keep the complete extracted code directory")
    # 中文：直接加载包内 src，不要求研究者执行 pip install .。
    # English: import the bundled source directly; the project need not be installed.
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    # 中文：字体缓存放在包内可写目录，兼容不允许写入用户主目录的环境。
    # English: keep the font cache writable in hosted/restricted notebook environments.
    cache = root / ".notebook_cache"
    cache.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    versions = _prepare_dependencies()
    # 中文：启用内嵌图片，保证每个模块的图像出现在输出单元格中。
    # English: explicitly activate inline figures for notebook module previews.
    try:
        from IPython import get_ipython
    except ImportError:
        shell = None
    else:
        shell = get_ipython()
    if shell is not None and getattr(shell, "kernel", None):
        shell.run_line_magic("matplotlib", "inline")
    package = import_module("nvpd_global")
    # 中文：避免内核误用以前安装的同名包；源路径必须属于当前解压目录。
    # English: detect a stale installed package rather than silently mixing releases.
    if Path(package.__file__).resolve().parent != (source / "nvpd_global").resolve():
        raise RuntimeError("内核已加载另一份 nvpd_global；请使用新内核打开此 notebook。"
                           " / Another nvpd_global release is loaded; use a fresh kernel.")
    inputs = package.bundled_data_dir()
    count = _verify_inputs(inputs)
    results_parent = root / "results"
    results_parent.mkdir(exist_ok=True)
    output = results_parent / ("global43_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    processing = json.loads((inputs / "processing.json").read_text(encoding="utf-8"))
    print(f"准备完成 / Ready: {count} samples; 0.009H; k=7.", flush=True)
    print("依赖版本 / Versions:", versions, flush=True)
    print("输出目录 / Output:", output, flush=True)
    return {"project_root": root, "input_dir": inputs, "output_dir": output,
            "versions": versions, "settings": processing}
