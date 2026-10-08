# Function reference / 函数接口说明

Default reproduction uses the notebook and its automatic startup. Advanced Python users can import computational functions from `nvpd_global`.

默认复现直接运行 notebook；以下接口说明供需要查看输入/输出或进行高级调用的使用者参考。

Import computational functions from `nvpd_global`. Functions do not write files unless their names explicitly describe loading, saving, or export. Plot functions live in `nvpd_global.plotting` and return Matplotlib figures; `save_figure` writes a PNG and closes the figure.

| Function | Input | Output |
| --- | --- | --- |
| `bundled_data_dir()` | No arguments | Installed/extracted package data directory containing 43 matching point/normal pairs |
| `preprocess(input_dir, output_dir=None, ...)` | Input directory, mode/resolution, optional catalog and display/export switches | Preprocessed `Stage`; oriented k=7 normals and all-sample cloud preview |
| `compute_nvpd(data)` | Preprocessed stage | New stage with `.raw` NVPDs and all-sample preview |
| `align_nvpd(nvpd)` | Raw-NVPD stage | New stage with `.aligned`, `.anchors`, profiles; alignment previews |
| `smooth_nvpd(aligned)` | Aligned stage | New stage with `.smoothed`; azimuth-only smoothing preview |
| `compute_distances(smoothed)` | Smoothed stage | New stage with `.distance`; distance-matrix preview |
| `cluster_hca(distances, manual_k=None)` | Distance stage | New stage with `.hca`; dendrogram and silhouette preview |
| `compare_clusters(clusters)` | Clustered stage | New stage with `.cluster_profiles`; mean/within/between previews |
| `save_results(comparison)` | Compared stage | Full numerical/figure export and result dictionary |
| `Config(...)` | Primary parameters, optional `manual_k` | Validated immutable configuration |
| `load_samples(directory, mode, config, sample_table)` | Data folder, input mode, config, optional catalog CSV | Alphabetically ordered `list[Sample]` with points, normals, metadata and display IDs |
| `voxel_downsample(points, coefficient)` | Finite `N×3` points, proportional voxel coefficient | `(M×3 points, metadata)` with original height and voxel side |
| `estimate_normals(points, k=7, block_size=2000)` | Voxelized `N×3` cloud, neighborhood including self | Oriented unit normals `N×3` |
| `orient_normals(points, normals)` | Matching `N×3` arrays | Centroid-oriented normals, preserving input lengths |
| `spherical_angles(normals)` | `N×3` nonzero normals | `(theta, phi)` in degrees, each length N |
| `normal_distribution(normals)` | Nonzero normals | Normalized `180×360` probability matrix |
| `align_facade_peak(matrix, band=(80,100), peak_window=5)` | Unsmoothed NVPD | `(aligned_matrix, diagnostics)` including anchor, original profile and peak-search profile |
| `smooth_azimuth(matrix, width=5)` | Aligned NVPD | Circularly smoothed and normalized `180×360` NVPD |
| `js_distance_matrix(matrices)` | Unit-mass `N×180×360` distributions | Symmetric `N×N` √JSD matrix, base 2 |
| `average_hca(distance, candidate_k=tuple(range(2,9)), manual_k=None)` | Symmetric distance matrix, candidate cuts | `HCAResult`: linkage tree, selected labels, per-sample silhouettes, scores/cuts, best and selected k, cut height, cophenetic correlation |
| `silhouette_values(distance, labels)` | Distance matrix and N cluster labels | N silhouette values; singleton 0 |
| `distance_contribution(p,q,distance)` | Two NVPDs and their matching √JSD | Binwise distance allocation, same shape; sum equals distance |
| `cluster_profiles(matrices,distance,labels)` | Final NVPDs, pairwise distances, labels | Dictionary `means`, `within`, `between` with all-member/all-pair maps and pair counts |
| `build_representations(samples, config)` | Ordered samples and config | `Representations`: raw/aligned/smoothed arrays, anchors, original/search profiles |
| `export_results(samples, representations, distance, hca, profiles, output, config, ...)` | Computed stages and new/empty output folder | Output `Path`; writes CSV, JSON, NPY/NPZ and optional figures |
| `run_global(samples, output, config, ...)` | Samples, output folder, config | Dictionary containing all stages and output path |

Export switches: `make_plots=True`, `individual_images=True`, `save_point_arrays=False`. Point-array export is opt-in. Run outputs may contain representations derived from restricted inputs; their distribution needs the input rights holder's permission.

Typical plotting functions: `point_cloud_atlas(samples)`, `nvpd_atlas(matrices,samples,title,vmax=None)`, `peak_atlas(representations,samples)`, `distance_figure(distance,samples)`, `hca_figure(hca,samples)`, `silhouette_figure(hca)`, `profile_figure(profiles,kind="means" or "within")`, `between_figure(profiles)`. `plot_all(...)` saves the complete figure set.

`sample_id` is a catalog/display identifier, not an array index. Every matrix, normal vector and label must preserve its matching input order. Supplied prepared normals bypass estimation and orientation; only use that mode when preprocessing is already complete.
