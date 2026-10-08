# NVPD：论文复现代码

[English](README.md) | [简体中文](README_zh.md)

本仓库提供论文 *A Computational Morphology Framework for Cultural Heritage Point Clouds via Normal Vector Probability Distributions* 的 **43 样本全量主实验复现代码**（原稿 3.2.1）。已包含论文使用的 **43 份 0.009H 点云及对应的 k=7 法向**，解压后可直接运行 notebook。不含敏感性分析、消融、其他两个实验和原始 OBJ。

敏感性分析代码因体量较大、属于参数验证的补充实现而未公开，可向第一作者 Zizhan Zhang（zhangzizhan@tju.edu.cn）合理请求获取。组件分割文件因版权及知识产权限制不公开，可向通讯作者 Yingchun Cao（yc_cao@163.com）合理请求获取。原始 OBJ 原则上不公开，任何访问需数据提供方授权，并与通讯作者协商。

代码采用 [PolyForm Noncommercial 1.0.0](LICENSE)：允许非商业科研、复现、修改和分享；商业使用需另行授权。这是限制商业使用的公开源代码许可。包内数据适用独立的[非商业科研使用条款](DATA_TERMS.md)，依赖库保留各自的许可。

## 关联论文与引用

Zizhan Zhang, Yingchun Cao and Yan Li. *A Computational Morphology Framework for Cultural Heritage Point Clouds via Normal Vector Probability Distributions.*

在研究中使用本方法、代码或数据时，请引用论文并注明代码版本。论文正式出版后补充出版信息和 DOI。代码咨询联系第一作者 Zizhan Zhang（zhangzizhan@tju.edu.cn）；正式数据请求联系通讯作者 Yingchun Cao（yc_cao@163.com）。

## 使用方式

**解压完整代码包 → 打开 `examples/global43.ipynb` → 选择“运行全部 / Run All”。**

1. 在[仓库首页](https://github.com/Z3-Lab/nvpd)点击 **Code → Download ZIP**，下载并完整解压。
2. 使用 Jupyter 或 VS Code 打开 [examples/global43.ipynb](examples/global43.ipynb)，选择 Python 3.10 或以上的内核。
3. 点击 **Run All / 运行全部**，依次查看各模块的图像与统计结果。结果自动保存至代码目录的 `results/` 下。

不需要执行安装命令、填写路径、下载数据或设置实验参数。首个代码块自动找到本地代码，检查/安装依赖，验证全部输入文件并创建输出路径；后续八个代码块逐模块完成计算、展示图像及结果保存。

使用 Python 3.10 或以上的 Jupyter/VS Code notebook 内核。首次缺少 NumPy、SciPy 或 Matplotlib 时会自动安装，需要联网且当前 Python 环境可写；依赖齐全时可离线运行。默认不需要原始 OBJ、Open3D 或 GPU。

包内数据位于 `src/nvpd_global/datasets/hebei43_0_009H/`，包含 86 个 NPY 文件、样本表、处理元数据及 SHA256 校验值。每次运行自动保存到 `results/global43_时间戳/`，不覆盖旧结果。详细说明见 [中英文使用指南](docs/USAGE_zh_en.md)。

每个模块封装成一个函数。notebook 每个代码块只调用对应模块，算法循环、画图和统计细节都在库内部。

## 跨设备运行与验证

默认流程使用相对路径、包内数据和 CPU 计算，不依赖作者电脑的目录或 macOS 专属命令。请把完整解压目录放在可写位置，使用带有 `pip` 的 Python 3.10+ notebook 内核；自动启动负责准备实验依赖，Python/Jupyter 本身需已能正常使用。

已在 macOS、Python 3.10.19 上验证：

- 独立解压后实际运行 Jupyter 的“运行全部”，不安装项目、不修改 notebook：显示 11 张内嵌图，保存 140 张 PNG。
- 在最初没有 NumPy、SciPy、Matplotlib 和 Open3D 的独立环境中，自动安装依赖并执行全部 notebook 代码块成功。安装版本为 NumPy 2.2.6、SciPy 1.15.3、Matplotlib 3.10.9，始终未安装 Open3D。
- 代码包改名并放在含中文、空格的路径下，完整运行成功。903 对样本距离与参考结果完全一致，自动选出三簇，大小为 4、5、34。

Windows、Linux 按同一流程设计，但目前未实机运行验证。声明的依赖范围不代表所有系统、Python 版本及库组合都已测试；其他平台可能有细微浮点差异，可结合导出的版本记录核对距离与簇成员。

## 模块化流程与关键参数

以下是 notebook 中各模块的调用顺序，首块代码已自动完成导入和环境准备：

```python
data = preprocess(environment["input_dir"], output_dir=environment["output_dir"], input_mode="prepared")
nvpd = compute_nvpd(data)
aligned = align_nvpd(nvpd)
smoothed = smooth_nvpd(aligned)
distances = compute_distances(smoothed)
clusters = cluster_hca(distances)
comparison = compare_clusters(clusters)
result = save_results(comparison)
```

首块自动启动返回 `environment`，其中包含包内输入路径和本次输出路径；所有论文参数已预置，不需要下载数据或修改代码。每一步自动显示对应图像：全部点云 → 全部原始 NVPD → 对齐 NVPD 与峰值 → 平滑 NVPD → 距离矩阵 → 树状图与轮廓系数 → 簇均值与差异图。最后一块统一导出数值、图像和参数记录。

样本总表、输入数据和论文默认参数已放进库。notebook 使用 `input_mode="prepared"` 直接复用点云和法向；如需重新计算法向，可改成 `input_mode="voxel_points"`；外部原始 OBJ 使用 `input_mode="obj"`。默认自动创建带时间戳的输出目录，`output_dir` 可指定其他目录。

每一步返回新的结果对象，不覆盖上一步。比如 `nvpd.raw`、`aligned.aligned`、`smoothed.smoothed` 是各阶段矩阵，`distances.distance` 是距离矩阵，`clusters.hca.labels` 是簇标签。

本仓库已包含 **0.009H** 的论文主实验输入。下载本仓库即可获取主实验的全部配套输入。这里的 `H` 是原始样本的高度，体素边长为系数乘以 `H`。已体素化的数据直接输入，不能再次体素化。`prepared` 模式加载已经求好的法向，要求点与法向逐行对应、方向已矫正。

论文主参数是 `0.009H`、PCA `k=7`（含自身）、1° 分箱、极角 `[80°,100°)` 的峰值对齐，然后 `1×5` 循环重叠方位平滑。平滑后依旧是 **180×360**。HCA 采用平均链接，默认在有效的 `k=2..8` 切分中选择平均轮廓系数最大值。当前论文分为三簇，大小为 4、5、34；平均轮廓系数约 0.11778668。

`cluster_hca(distances, manual_k=3)` 可手动指定三簇，导出结果会标明是手动选择，并保留自动最优值。树状图颜色与切线使用实际选择的分簇数。

## 输出

每次使用新结果目录，避免多次运行的文件混杂。

- `samples.csv`：编号、样本名、点数、峰值角度、簇号和轮廓系数。
- `sqrt_jsd_matrix.csv`、`silhouette_by_k.csv`、`linkage.csv`：距离、选簇与树结构。
- `arrays/`：分箱、对齐、平滑的全部矩阵，以及簇均值和差异矩阵。
- `summary.json`：参数、输入哈希、依赖版本、簇成员、代表样本及比较统计。
- `figures/`：全部样本的点云、三个 NVPD 阶段、对齐峰值、距离矩阵、HCA、轮廓系数、簇均值、簇内差异、簇间差异。
- `figures/samples/`：每个样本三个阶段的独立图像。

簇均值使用全部成员；簇内差异使用全部无序样本对；簇间差异使用两个簇的全部交叉样本对。红色表示前一个簇在该角度有更多概率，蓝色表示后一个簇有更多概率；白色也可能来自正负抵消。**无符号**贡献矩阵用于统计差异大小，符号图用于观察方向。色彩的非线性增强只改变显示，不改变计算数据。

更多安装示例、输入格式和指标解释见[英文说明](README.md)；逐模块的中英文使用说明见[使用指南](docs/USAGE_zh_en.md)，详细函数接口见[API 文档](docs/API.md)。代码许可见 [LICENSE](LICENSE)，数据使用条款见 [DATA_TERMS.md](DATA_TERMS.md)。
