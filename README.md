# NVPD: paper reproduction code

[English](README.md) | [简体中文](README_zh.md)

A small Python package for the **primary global comparison of 43 Hebei pagodas** in *A Computational Morphology Framework for Cultural Heritage Point Clouds via Normal Vector Probability Distributions*.

This package contains proportional voxel preprocessing, PCA normals, NVPD construction, facade-peak alignment, azimuthal smoothing, base-2 Jensen–Shannon distance, average-linkage hierarchical clustering, and angular difference maps. It includes a module-by-module reproduction notebook and numerical/PNG exports. It does not contain the directional-window or base/body experiments, sensitivity sweeps, ablations, test scripts, or source OBJ models.

This repository provides the reproduction code for the paper's **43-sample primary global experiment**. The paper-resolution point clouds and matching normals are bundled so the notebook can run directly after extraction. The other two case experiments and supplementary parameter studies are outside this release.

**License:** [PolyForm Noncommercial 1.0.0](LICENSE). Noncommercial research, reproduction, modification and sharing are permitted under the license; commercial use requires separate permission. This is source-available software under a noncommercial license. Bundled data have separate [noncommercial research terms](DATA_TERMS.md); source OBJ models are not included. Dependency licenses remain unchanged.

## Associated paper and citation

Zizhan Zhang, Yingchun Cao and Yan Li. *A Computational Morphology Framework for Cultural Heritage Point Clouds via Normal Vector Probability Distributions.*

Please cite this paper when using the method, code or data in research, and identify the code version. Publication details and a DOI will be added when available. Code and bundled-data enquiries: Zizhan Zhang (`zhangzizhan@tju.edu.cn`).

## Start here: open the notebook and Run All

1. Extract the **entire archive**, retaining its folder structure.
2. Open [examples/global43.ipynb](examples/global43.ipynb) in a Python 3.10+ Jupyter or VS Code notebook kernel.
3. Select **Run All**. Do not edit paths or parameters or run installation commands.

The first cell automatically finds local source, checks the three core dependencies, installs missing/incompatible libraries into the active kernel, verifies all 86 bundled input hashes, and enables inline figures. A new `results/global43_timestamp/` directory is selected automatically. The remaining eight cells call one function per module, display their figures and save the complete result.

First use needs internet and a writable Python environment only if dependencies are missing. With compatible NumPy/SciPy/Matplotlib available, the experiment runs offline. No project installation, raw OBJ, Open3D or GPU is required for the default notebook. Supported baselines are NumPy 1.24+, SciPy 1.10+, and Matplotlib 3.7+ within the declared major-version bounds; the exact verified reference environment is recorded in `requirements-reproduction.txt` and run summaries.

See [docs/USAGE_zh_en.md](docs/USAGE_zh_en.md) for detailed bilingual instructions. The optional CLI below is for users who prefer a terminal; it is not a prerequisite for the notebook.

## Portability and verification

The default notebook uses relative paths, bundled data and standard CPU libraries. It has no macOS-specific commands or dependence on the author's directories. Keep the complete extracted folder in a writable location and use a working Python 3.10+ notebook kernel with `pip` available; automatic setup prepares experiment dependencies, not Python/Jupyter itself.

Verified on macOS with Python 3.10.19:

- An actual Jupyter Run All from an independently extracted archive, without project installation or notebook edits: 11 inline figures and 140 saved PNGs.
- A separate environment initially containing none of NumPy, SciPy, Matplotlib or Open3D: automatic dependency installation and execution of all notebook code cells succeeded with NumPy 2.2.6, SciPy 1.15.3 and Matplotlib 3.10.9. Open3D remained absent.
- The extracted package was renamed and placed in a path containing spaces and Chinese characters. All 903 pairwise distances matched the reference exactly; the selected three clusters had sizes 4, 5 and 34.

Windows and Linux are intended to use the same workflow, but have not been executed in this verification. The declared dependency range does not mean every operating system, Python version or library combination has been tested. Small floating-point differences on other platforms are possible; compare distances and memberships, and retain the exported version information.

## Data and resolution

This distribution includes all **43 paper-resolution 0.009H point clouds and matching k=7 normals** in `src/nvpd_global/datasets/hebei43_0_009H/`. `bundled_data_dir()` finds them both in the extracted source tree and after package installation. All 86 NPY files have a SHA256 manifest and sample catalog. The notebook is preconfigured to use these inputs.

| Input | Meaning | Paper-result status |
| --- | --- | --- |
| Bundled `0.009H` clouds with `k=7` normals | Primary experiment inputs, included in this package | Default notebook reproduces the paper's numerical global results |
| Manually cleaned OBJ | Authorized, upright, individual pagoda meshes | Optional input for regenerating the `0.009H` clouds; not bundled |

`H` is the original input's vertical extent, `max(z)-min(z)`. A voxel side is `coefficient × H`; it is **not** computed again when loading already voxelized data. The included `0.009H` arrays are already prepared; do not voxelize them again. Original OBJ access enquiries should be directed to corresponding author Yingchun Cao (`yc_cao@163.com`).

All inputs must be manually cleaned to remove unrelated objects and have their vertical axis along `+z`. This package does not implement photogrammetric reconstruction, quality management, or axis correction. Sampling mesh vertices followed by voxel averaging follows the paper; it is not equal-area surface sampling.

## Run the complete primary workflow

Optional terminal workflow: install with `python -m pip install .` first. Notebook users can skip this section entirely.

```bash
# Bundled paper inputs: source-directory command, reuse matching normals.
nvpd-global --input src/nvpd_global/datasets/hebei43_0_009H --input-mode prepared \
  --samples src/nvpd_global/datasets/hebei43_0_009H/samples.csv \
  --voxel-coefficient 0.009 --output /path/to/results_bundled

# Paper resolution: already voxelized clouds, recalculate PCA normals.
nvpd-global --input /path/to/0.009H/clouds --input-mode voxel_points \
  --samples examples/hebei43.csv --voxel-coefficient 0.009 --output /path/to/results_paper

# Regenerate preprocessing from authorized manually cleaned OBJ files.
nvpd-global --input /path/to/obj --input-mode obj \
  --samples examples/hebei43.csv --voxel-coefficient 0.009 --output /path/to/results_obj
```

Use a new or empty output directory for each run. `--no-individual-images` omits separate per-sample images while retaining all-sample atlases; `--no-figures` exports numbers only. Inputs are not copied to the output unless `--export-point-arrays` is explicitly enabled. `--manual-k 3` requests a particular valid cut; the default uses the highest mean silhouette among valid cuts in `k=2..8`.

Input modes:

| Mode | Preprocessing performed |
| --- | --- |
| `obj` | Read face-referenced vertices, proportional voxelization, PCA, centroid orientation |
| `raw_points` | Proportional voxelization, PCA, centroid orientation |
| `voxel_points` | Skip voxelization; PCA and centroid orientation |
| `prepared` | Load matching points and already oriented normals; skip voxelization and PCA |

Supported point formats: `<sample>_points.npy` (`N×3`, no pickled objects), `.xyz`, `.txt`, `.ply`. Prepared mode additionally requires `<sample>_normals.npy` in identical point order. Optional CSV columns `points_file` and `normals_file` allow relative filenames. A catalog can declare `voxel_coefficient` and `normal_k`; these are checked against the requested configuration. Without a catalog the supplied resolution is a user declaration, not something inferred from coordinates. `examples/hebei43.csv` supplies the paper's sample IDs; internal arrays follow alphabetical sample names. Always consult the exported `samples.csv` for array order.

## Module API (optional advanced use)

Open [examples/global43.ipynb](examples/global43.ipynb) and select Run All. Startup is automatic, and each module has its own short code cell and displays its corresponding results automatically. Algorithms, loops, plotting, and export details stay inside the library.

```python
from nvpd_global import (bundled_data_dir, preprocess, compute_nvpd, align_nvpd, smooth_nvpd,
                         compute_distances, cluster_hca, compare_clusters, save_results)

INPUT_DIR = bundled_data_dir()
VOXEL_COEFFICIENT = 0.009  # resolution of the bundled paper inputs

data = preprocess(INPUT_DIR, voxel_coefficient=VOXEL_COEFFICIENT, input_mode="prepared")
nvpd = compute_nvpd(data)
aligned = align_nvpd(nvpd)
smoothed = smooth_nvpd(aligned)
distances = compute_distances(smoothed)
clusters = cluster_hca(distances)
comparison = compare_clusters(clusters)
result = save_results(comparison)
```

The paper's 43-sample catalog is bundled, so no catalog loading code is needed. `preprocess` carries the configuration, samples, and a timestamped output directory into each following stage. Each function returns a new `Stage` object: `nvpd.raw`, `aligned.aligned`, `smoothed.smoothed`, `distances.distance`, and `clusters.hca` expose numerical results without overwriting earlier stages.

Each stage displays its own figures in Jupyter: all-sample clouds, raw NVPDs, aligned NVPDs and peak profiles, smoothed NVPDs, the distance matrix, HCA and silhouettes, and cluster means/differences. `save_results` writes the entire result to disk. Parameters, sample order and input provenance are exported automatically.

The notebook explicitly uses `input_mode="prepared"` to load bundled matching normals. For recalculation, use `input_mode="voxel_points"` (the function default), with k=7 PCA and centroid orientation; use `input_mode="obj"` to voxelize authorized external meshes first. `output_dir` sets a new/empty result folder; `display=False` suppresses notebook previews; `make_plots=False` omits saved images. `cluster_hca(distances, manual_k=3)` allows a manually selected cut while preserving the automatic best k in the result.

## Primary parameters and conventions

| Step | Paper setting and meaning |
| --- | --- |
| Voxelization | `0.009H`; Open3D voxel averaging of face-referenced mesh vertices |
| PCA | `k=7`, **including the query point**; smallest covariance eigenvector |
| Orientation | Flip if the normal's dot product with point minus cloud centroid is negative |
| Mapping/binning | Polar angle from `+z`, azimuth from `+x`; 1° bins; one vote per normal |
| NVPD | `180×360` (polar rows × azimuth columns); divide counts by total count |
| Peak alignment | Sum polar rows `[80°,100°)`; circular five-column average for peak search only; shift the full unsmoothed NVPD to place its largest peak at 0° |
| Smoothing | After alignment; circular overlapping `1×5` average, stride one; keep `180×360`; normalize total probability |
| Distance | `sqrt(JSD)` with logarithm base 2; SciPy `jensenshannon` already returns the square root |
| HCA | Average linkage; compare valid `k=2..8` cuts by mean silhouette; tied scores choose smaller `k` |

Peak alignment defines a prominent facade reference. It does not prove exact physical correspondence of facades. These histograms represent probability per angular bin, not density per unit spherical area.

With the reference `0.009H`, `k=7` data, the current paper result selects `k=3`, with cluster sizes `4, 5, 34` and mean silhouette approximately `0.11778668`. Cluster numbers are computational labels; comparisons across datasets should use membership, not label numbers alone. Numerical reproduction also depends on the input clouds, mesh reading, and library versions.

## Outputs and interpretation

| Output | Content / how to read |
| --- | --- |
| `samples.csv` | IDs, names, point counts, peak anchors, cluster labels, individual silhouettes, declared input resolution |
| `sqrt_jsd_matrix.csv` | Symmetric all-pair distances in `[0,1]`; larger means more different normal distributions |
| `silhouette_by_k.csv` | Relative within-cluster compactness and between-cluster separation; higher is preferable among examined cuts, not proof of a correct architectural type |
| `linkage.csv` | SciPy tree merge nodes, heights, and member counts |
| `summary.json` | Parameters, versions, input hashes, selected cut, member lists, medoids, pair counts, and regional unsigned contributions |
| `arrays/*.npy` | Raw/aligned/smoothed `N×180×360` matrices, profiles, anchors, distances, labels |
| `arrays/cluster_profiles.npz` | All-member means, within-cluster maps, signed and unsigned between-cluster maps |
| `figures/01..11_*.png` | Input-cloud atlas; raw/aligned/smoothed NVPD atlases; peak profiles; distance matrix; dendrogram; silhouette curve; cluster means; within/between difference maps |
| `figures/samples/*.png` | Raw, aligned, and smoothed NVPD for every sample |

All HCA branch colors and the cut line correspond to the selected `k`. A sample's silhouette can be negative; a singleton receives zero. Low mean silhouettes should be interpreted with architectural observations rather than described as strongly separated types.

Cluster means average **all** member NVPDs. Within-cluster maps average all unordered member pairs. Between-cluster maps average every cross-cluster pair. For distributions `p,q`, binwise JSD terms `c_b` sum to `d²`; the exported distance contribution `c_b/d` sums to their Jensen–Shannon distance `d`. Identical pairs contribute zero. Unsigned averaged maps sum to the corresponding mean pair distance. The signed map multiplies each bin contribution by `sign(p_b-q_b)` before averaging: red means the first cluster has more probability, blue means the second. White may indicate small differences **or cancellation** across pairs; use unsigned maps for magnitudes. The sign is not proximity to a cluster and the maps are not causal attributions.

Probability maps use `magma_r`; signed maps use blue–white–red. Gamma `0.3` display transforms reveal weak angular structure without changing saved probabilities or contributions. Raw/aligned/smoothed atlases share a common probability scale; each cluster-map figure shares its own scale. Input-cloud figures use deterministic visual subsampling only; analysis uses all points.

See [docs/API.md](docs/API.md) for function inputs and outputs and [README_zh.md](README_zh.md) for a Chinese quick guide. Cite the associated manuscript when using the method; add the final publication DOI when available.
