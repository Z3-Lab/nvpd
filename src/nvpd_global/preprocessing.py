"""Face-referenced mesh vertices, proportional voxels and PCA normal estimation."""
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def xyz_array(values, name="points"):
    """中文：输入为非空 N×3 数组，返回有限的 float64 数据。只检查类型、维度与数值，不平移、旋转或归一化几何坐标。

    English:
    Return a finite, nonempty float64 N x 3 array, without changing coordinates.
    """
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 3 or not len(values) or not np.isfinite(values).all():
        raise ValueError(f"{name} must be a finite, nonempty N x 3 array")
    return values


def _open3d():
    try:
        import open3d
    except ImportError as error:
        raise ImportError("Install the mesh extra: pip install '.[mesh]' for OBJ/PLY/voxelization") from error
    return open3d


def load_points(path):
    """中文：读取 NPY、XYZ/TXT 或 PLY 坐标。NPY 使用 allow_pickle=False；识别 Git LFS 指针，避免把未下载的占位文件当作真实点云。

    English:
    Load NPY, whitespace XYZ/TXT, or PLY; NPY must contain only XYZ columns.
    """
    path = Path(path)
    with path.open("rb") as stream:
        is_pointer = stream.read(40).startswith(b"version https://git-lfs.github.com/spec")
    if is_pointer:
        raise ValueError(f"{path.name} is a Git LFS pointer, not the point-cloud file")
    if path.suffix.lower() == ".npy":
        values = np.load(path, allow_pickle=False)
    elif path.suffix.lower() in (".xyz", ".txt"):
        values = np.loadtxt(path, ndmin=2)
    elif path.suffix.lower() == ".ply":
        values = np.asarray(_open3d().io.read_point_cloud(str(path)).points)
    else:
        raise ValueError("Supported point formats: .npy, .xyz, .txt, .ply")
    return xyz_array(values)


def face_referenced_vertices(path):
    """中文：仅保留 OBJ 三角面引用的顶点，并保持原顶点索引顺序。输入应已人工清理且竖直方向为 +z；不做等面积采样或自动质量管理。

    English:
    Extract unique vertex indices referenced by OBJ triangles, preserving index order.
    
    Input must already be manually cleaned and have its vertical axis along +z.
    This function does not perform the author's manual quality-control step.
    No area sampling, mesh simplification or density weighting is applied.
    """
    mesh = _open3d().io.read_triangle_mesh(str(path), enable_post_processing=False)
    triangles = np.asarray(mesh.triangles)
    if not len(triangles):
        raise ValueError(f"No triangles found in {Path(path).name}")
    return xyz_array(np.asarray(mesh.vertices)[np.unique(triangles.ravel())]).copy()


def voxel_downsample(points, coefficient=0.009):
    """中文：原始点云的高度 H=max(z)-min(z)，体素边长为 coefficient×H。Open3D 输出每个体素内点的均值，不是体素中心。返回点云和实际尺寸元数据；不要对已经体素化的数据重复调用。

    English:
    Average points within Open3D voxels of side coefficient * original z extent.
    
    Returns (voxel_points, metadata). Scale is handled proportionally; coordinates
    are not rescaled or rotated. Output points are voxel means, not voxel centres.
    Only use this function on raw, not already voxelized, points.
    """
    points = xyz_array(points)
    height = float(np.ptp(points[:, 2]))
    if not np.isfinite(coefficient) or coefficient <= 0 or height <= 0:
        raise ValueError("A positive coefficient and positive vertical extent are required")
    o3d = _open3d()
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    result = np.asarray(cloud.voxel_down_sample(coefficient * height).points).copy()
    return result, {"source_height": height, "voxel_side_length": coefficient * height,
                    "source_point_count": len(points), "voxelization_applied": True}


def orient_normals(points, normals):
    """中文：输入点和法向必须逐行对应。计算每点相对整体质心的向量，点积为负时反转法向。保留法向长度及点序；凹面上此约定不保证等于物理外法向。

    English:
    Flip each PCA normal to have nonnegative dot product with point minus centroid.
    
    This is the paper's centroid-outward convention, not a guarantee of the true
    exterior direction at concave surfaces. Returns normals in original point order.
    """
    points, normals = xyz_array(points), xyz_array(normals, "normals").copy()
    if points.shape != normals.shape:
        raise ValueError("Points and normals must have identical shapes")
    length = np.linalg.norm(normals, axis=1)
    if np.any(length == 0):
        raise ValueError("Normals must not contain zero vectors")
    radial = points - points.mean(axis=0)
    normals[np.einsum("ij,ij->i", normals, radial) < 0] *= -1
    return normals


def estimate_normals(points, k=7, block_size=2000):
    """中文：输入为体素点云；k=7 包含点自身。对每个 k 近邻集合去均值，构造 3×3 协方差矩阵，最小特征值对应的单位特征向量为 PCA 法向，再做质心朝向矫正。按块求解仅降低临时内存，输出 N×3 法向与输入逐行对应。

    English:
    PCA normal from the minimum eigenvector of each k-neighbour covariance.
    
    Neighbours include the point itself. Query all points using cKDTree with
    workers=1; process covariances in blocks to bound temporary memory. Normals
    are returned as centroid-oriented N x 3 vectors, in the input point order.
    """
    points = xyz_array(points)
    if not isinstance(k, int) or k < 3 or len(points) <= k or block_size < 1:
        raise ValueError("Require integer k >= 3, more than k points, and positive block_size")
    # k 包括查询点自身；固定单线程邻域查询 / k includes self; deterministic single-worker query.
    indices = cKDTree(points).query(points, k=k, workers=1)[1]
    normals = np.empty_like(points)
    for start in range(0, len(points), block_size):
        neighbourhood = points[indices[start:start + block_size]]
        neighbourhood -= neighbourhood.mean(axis=1, keepdims=True)
        # 每个邻域得到3×3协方差 / One 3x3 covariance per centered neighborhood.
        covariance = np.einsum("nki,nkj->nij", neighbourhood, neighbourhood) / k
        _, vectors = np.linalg.eigh(covariance)
        # eigh 按特征值升序返回列向量 / eigh orders eigenvectors by ascending eigenvalue.
        normals[start:start + block_size] = vectors[:, :, 0]
    return orient_normals(points, normals)
