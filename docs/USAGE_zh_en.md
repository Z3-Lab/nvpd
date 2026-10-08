# 使用说明 / User guide

## 1. 开始运行 / Start

解压完整压缩包，在 Python 3.10+ 的 Jupyter 或 VS Code 中打开 `examples/global43.ipynb`，点击 **运行全部 / Run All**。保持 `notebook_setup.py`、`src/`、`examples/` 的相对位置；不需要填写目录、参数或运行安装命令。

Extract the complete archive, open `examples/global43.ipynb` in a Python 3.10+ notebook kernel in Jupyter or VS Code, and click **Run All**. Keep `notebook_setup.py`, `src/`, and `examples/` in their extracted positions. No directory/parameter changes or installation commands are needed.

启动会自动找到当前代码、复用兼容依赖或安装缺失依赖，校验 43 例点云和法向，启用内嵌图并确定结果目录。缺少依赖时需要联网及可写环境；依赖齐全时可离线运行。这里的自动准备不代替 Python/Jupyter 本身，使用者需要能够打开并运行 notebook。

Startup finds this code, reuses compatible libraries or installs missing ones, verifies all 43 point/normal pairs, enables inline plots, and selects the result directory. Missing libraries require internet and a writable Python environment; otherwise execution can be offline. Automatic startup does not install Python/Jupyter itself: a working notebook kernel is the prerequisite.

跨设备验证：已在 macOS/Python 3.10.19 的独立空环境中自动安装 NumPy 2.2.6、SciPy 1.15.3、Matplotlib 3.10.9 并执行全部代码块，未安装 Open3D；中文和空格路径通过，903 对距离与参考完全一致，保存 140 张图。另已完成实际 Jupyter 运行全部及内嵌图验证。Windows/Linux 尚未实机验证；完整解压目录及当前 Python 环境需要可写，内核需提供 pip。

Portability verification: all code cells passed in a separate macOS/Python 3.10.19 environment after automatically installing NumPy 2.2.6, SciPy 1.15.3 and Matplotlib 3.10.9, without Open3D. Chinese characters and spaces in paths worked; all 903 distances matched the reference exactly and 140 figures were saved. Actual Jupyter Run All and inline displays were also verified separately. Windows/Linux have not yet been executed. The extracted directory and active Python environment must be writable, and the kernel must provide pip.

## 2. 复现范围与数据 / Scope and inputs

本入口完整复现全量 43 样本主实验（原稿 3.2.1）：读取预处理结果、构建 NVPD、峰值对齐、方位平滑、√JSD、平均链接 HCA、簇特征/差异图及完整导出。不包含其他两个论文实验、敏感性扫描或消融脚本。

This entry reproduces the complete primary global experiment (former Section 3.2.1): prepared-data loading, NVPD, peak alignment, azimuthal smoothing, √JSD, average HCA, cluster characteristics/differences and full export. It does not include the other two experiments, sensitivity sweeps or ablation scripts.

包内数据是 0.009H 体素点云及 k=7 质心朝向矫正法向，不是单独公开仓库中的 0.025H 粗分辨率数据。每例的点和法向逐行对应，默认 prepared 模式直接复用；不重复体素化。自动校验 samples.csv 中的分辨率、邻域、文件名及 SHA256。

Bundled inputs are 0.009H voxel clouds with k=7 centroid-oriented normals, not the separate 0.025H demonstration clouds. Within each sample, points and normals correspond row by row. Prepared mode reuses these arrays without repeated voxelization. Resolution, neighborhood, filenames and SHA256 hashes are verified automatically.

## 3. 每块输入和输出 / Module inputs and outputs

| 模块 / Module | 输入 / Input | 输出 / Output |
| --- | --- | --- |
| 自动启动 / Setup | 完整解压目录 / Extracted directory | 依赖、输入验证、environment路径 / Libraries, integrity check, environment paths |
| preprocess | 43组点与法向 / 43 prepared pairs | data.samples、全部点云图 / Samples and cloud atlas |
| compute_nvpd | data.samples[i].normals | nvpd.raw：43×180×360、总概率1 / Raw probabilities and atlas |
| align_nvpd | 原始矩阵 / Raw NVPDs | aligned.aligned、锚点及峰曲线 / Aligned arrays, anchors, diagnostics |
| smooth_nvpd | 对齐矩阵 / Aligned NVPDs | smoothed.smoothed：同尺寸 / Same-size smoothed probabilities |
| compute_distances | 最终分布 / Final NVPDs | distances.distance：43×43、903对 / Distance matrix and 903 pairs |
| cluster_hca | √JSD矩阵 / Distance matrix | clusters.hca：树、标签、分数、阈值 / Tree, labels, scores, cut |
| compare_clusters | 最终矩阵、簇标签 / Final matrices and labels | 簇均值、全部样本对贡献 / All-member means and all-pair maps |
| save_results | 上述结果 / All stages | CSV/JSON/NPY/NPZ、140张PNG / Full numerical and figure export |

每个模块返回新阶段对象，上一步仍可查看。矩阵中的样本顺序与导出 samples.csv 一致；显示编号不是 Python 下标。

Each module returns a new stage, preserving earlier results. Array order matches the exported samples.csv; display IDs are not Python indices.

## 4. 看图 / Reading the figures

- **01 点云 / Clouds:** 全部43例；显示抽点与缩放仅用于展示，不修改分析输入。 / All samples; visual subsampling/scaling does not change analysis inputs.
- **02–04 NVPD:** 原始、对齐、平滑；共用概率色标。γ=0.3只增强显示。 / Raw/aligned/smoothed distributions with a shared scale; gamma affects display only.
- **05 找峰 / Peaks:** 灰色原曲线，蓝色找峰均值，橙色虚线是对齐前锚点；该均值只找峰。 / Raw profile, peak-search average and anchor; this average only finds the peak.
- **06 距离 / Distances:** 数值越大表示分布越不同，零对角线是样本与自身。 / Larger means more different distributions; self-distance is zero.
- **07 HCA:** 样本编号对应样本表，分支色与虚线对应相同的选定分簇。 / IDs link to the sample catalog; branch colors and cut line represent the selected partition.
- **08 轮廓 / Silhouette:** 越高表示相对紧凑/分离更好；不是类型学准确率。 / Higher means relative compactness/separation, not typological accuracy.
- **09 簇均值 / Means:** 全部成员的平均概率分布；各簇共用色标。 / All-member mean probabilities on a shared scale.
- **10 簇内 / Within:** 全部无序簇内样本对的无符号距离贡献；越高是局部差异越大。 / Unsigned contributions across all within pairs; higher means greater local differences.
- **11 簇间 / Between:** 全部交叉样本对的有符号贡献；红色前簇概率更多、蓝色后簇更多，白色可能来自抵消。 / All cross-pair signed maps; red/blue show probability direction, white can reflect cancellation.

以无符号图统计差异大小，不能把有符号图总和当作簇间距离。极角90°附近的法向接近水平，常与竖直立面对应；其他角格的建筑含义应结合点云观察。

Use unsigned maps for magnitudes, not the sum of a signed map. Normals near polar angle 90° are near-horizontal and often associated with vertical facades; interpret other bins using geometric context.

## 5. 输出与复核 / Outputs and checks

输出自动位于代码目录 `results/global43_时间戳/`。包括样本结果表、距离表、候选k分数、树结构、全部阶段矩阵、簇贡献矩阵、参数/版本/哈希记录，以及140张PNG。复现时不用改路径；再次运行全部自动创建新目录。

Results are automatically saved under `results/global43_timestamp/`, including sample/distances/candidate-k/linkage tables, all intermediate matrices, cluster maps, settings/versions/hashes and 140 PNGs. No path changes are needed; another Run All creates a new directory.

参考结果自动选k=3，簇大小4、5、34，平均轮廓约0.11778668。这些结果在运行中重新求得，未强制指定。兼容平台/库版本的细微浮点差异可通过 summary.json 中的版本信息追溯。

The reference selects k=3 with sizes 4,5,34 and mean silhouette approximately 0.11778668. These are recomputed, not forced. Small platform/library floating-point differences are traceable through summary.json.

## 6. 常见运行情况 / Common situations

第一次依赖安装较慢时请等待启动块结束。数据哈希报错时重新下载并完整解压。复制过来的内核若已经加载另一份同名代码，使用新内核再运行全部，避免混用不同版本。只重复最后保存块会因目录已有结果而拒绝覆盖；需要新一轮结果时选择运行全部。

Allow automatic installation to finish on first use. For hash errors, redownload and fully extract. If a reused kernel has already loaded another release, use a fresh kernel and Run All to avoid mixing versions. Repeating only the final save cell refuses to overwrite a populated directory; use Run All for a new coherent run.
