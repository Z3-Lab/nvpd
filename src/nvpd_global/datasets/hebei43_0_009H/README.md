# 包内主实验数据 / Bundled primary experiment data

中文：此目录包含 43 例 0.009H 体素点云，以及逐点对应的 k=7 PCA 法向（已做质心朝向矫正），共 86 个 float64 N×3 NPY 文件。默认 notebook 自动读取它们，无需更改路径或另行下载。输入已经处理完成，不再体素化。

- `*_points.npy`：XYZ 坐标 / XYZ coordinates.
- `*_normals.npy`：同一行点对应的法向 / Normals matching each point row.
- `samples.csv`：编号、名称、系数、k、点数、文件名和哈希 / IDs, names, parameters, counts, filenames and hashes.
- `processing.json`：处理规则、版本和参考结果 / Conventions, reference versions and expected results.
- `checksums.sha256`：86 个数组的完整性校验 / Integrity checks for all arrays.

运行后参考结果为三簇，大小为 4、5、34，平均轮廓系数约 0.11778668。程序会重新计算结果而不是读取预设簇号。独立 0.025H 公开数据用于粗分辨率演示，本目录是论文使用的 0.009H 数据。

The reference run selects three clusters of sizes 4,5,34 with mean silhouette about 0.11778668; memberships are recomputed. This directory contains paper-resolution 0.009H inputs, distinct from the separate coarse 0.025H demonstration data.

These are the 43-sample inputs at the paper's **0.009H** voxel resolution, together with matching **k=7** centroid-oriented PCA normals. There are 86 NPY files; each contains a float64 N×3 array. Within each sample, points and normals correspond row by row.

- `*_points.npy`: prevoxelized XYZ coordinates.
- `*_normals.npy`: already estimated and oriented normal vectors.
- `samples.csv`: sample IDs, resolution, neighborhood, point counts, filenames and SHA256 hashes.
- `processing.json`: preprocessing conventions and expected primary global result.
- `checksums.sha256`: file-integrity checks.

Use `preprocess(bundled_data_dir(), input_mode="prepared", voxel_coefficient=0.009)` to load both arrays and reproduce the subsequent modules. To recompute normals from these same voxel clouds, use `input_mode="voxel_points"`. Do not voxelize these clouds again.

The global analysis uses 1° binning, facade-peak alignment, 1×5 azimuthal smoothing, base-2 √JSD and average linkage. The reference result selects three clusters of sizes 4, 5 and 34, with mean silhouette 0.11778668134068941.

Raw OBJ models, segmentation files and alternative parameter datasets are not included. This dataset is distinct from the separate 0.025H public demonstration dataset. These bundled derived data are available for noncommercial research, reproduction and teaching under `DATA_TERMS.md` at the repository root. Commercial use requires separate written permission. Original survey/model rights remain with their respective rights holders; this release does not grant access to or permission to reuse source OBJ models.

中文：本目录中的派生点云及法向允许非商业科研、复现和教学使用，详细条款见仓库根目录 `DATA_TERMS.md`。商用需另行获得书面授权。原始测绘及 OBJ 模型的权利由相应权利人保留，本次发布不授权获取或复用原始 OBJ。
