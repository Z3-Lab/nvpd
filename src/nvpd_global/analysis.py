"""Base-2 Jensen-Shannon distance and primary average-linkage HCA."""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from scipy.spatial.distance import jensenshannon, squareform
from scipy.cluster.hierarchy import linkage, fcluster, cophenet


def js_distance_matrix(matrices):
    """中文：输入 N×180×360 单位总质量分布。展平后逐对使用底数 2 的 Jensen–Shannon 距离；SciPy 已返回 √JSD，不要再开方。返回 N×N 对称矩阵、精确零对角线；距离范围 [0,1]。

    English:
    Return symmetric N x N sqrt(JSD_2), with exact zero diagonal.
    
    Each input distribution must be nonnegative and have unit total mass.
    scipy.jensenshannon returns the square root already: do not take it again.
    Zeros contribute zero to the divergence. Values lie in [0,1].
    """
    matrices = np.asarray(matrices, dtype=np.float64)
    if matrices.ndim != 3 or matrices.shape[1:] != (180, 360):
        raise ValueError("Expected N x 180 x 360 distributions")
    flat = matrices.reshape(len(matrices), -1)
    if not np.isfinite(flat).all() or np.any(flat < 0) or not np.allclose(flat.sum(axis=1), 1, atol=1e-12):
        raise ValueError("Distributions must be finite, nonnegative and normalized")
    result = np.zeros((len(flat), len(flat)), dtype=np.float64)
    for i, j in combinations(range(len(flat)), 2):
        # 此函数已开方；不再调用sqrt / Already a distance: do not take a second square root.
        result[i, j] = result[j, i] = jensenshannon(flat[i], flat[j], base=2)
    return result


def silhouette_values(distance, labels):
    """中文：a 为到同簇其他样本的平均距离，b 为到其他各簇平均距离的最小值；s=(b-a)/max(a,b)。单例簇取 0。值越高表示相对紧凑/分离更好，不直接证明建筑类型正确。

    English:
    Per-sample (b-a)/max(a,b), with singleton samples assigned zero.
    
    a is the mean distance to OTHER members of the same cluster; b is the
    smallest mean distance to any other cluster. Higher mean scores indicate
    relative compactness/separation, not typological correctness.
    """
    labels = np.asarray(labels)
    groups = np.unique(labels)
    if len(labels) != len(distance) or not 2 <= len(groups) < len(labels):
        raise ValueError("Silhouette requires 2..N-1 clusters and one label per sample")
    values = np.zeros(len(labels))
    for i, group in enumerate(labels):
        same = np.flatnonzero(labels == group)
        if len(same) == 1:
            continue
        a = distance[i, same[same != i]].mean()
        b = min(distance[i, labels == other].mean() for other in groups if other != group)
        values[i] = (b - a) / max(a, b) if max(a, b) else 0
    return values


@dataclass
class HCAResult:
    tree: np.ndarray
    labels: np.ndarray
    silhouette: np.ndarray
    scores: dict[int, float]
    cuts: dict[int, np.ndarray]
    best_k: int
    selected_k: int
    cut_height: float
    cophenetic_correlation: float


def average_hca(distance, candidate_k=tuple(range(2, 9)), manual_k=None):
    """中文：用预计算距离矩阵进行平均链接 HCA，对有效的 k=2…8 切分计算平均轮廓系数并选最大值；相同分数选较小 k。并列合并高度导致实际簇数不足的切分不参与选择。切线位于最后纳入与首个排除的合并高度之间，并核对其簇成员与选定 k 一致。

    English:
    Build average linkage and select k by silhouette over valid candidate cuts.
    
    maxclust can yield fewer clusters at tied merge heights; such cuts are
    omitted. The cut line is halfway between the last included and first excluded
    merge heights. Its partition is explicitly checked against the selected cut.
    Returned tree is SciPy's (N-1) x 4 linkage matrix; labels are one-based.
    """
    distance = np.asarray(distance, dtype=np.float64)
    if distance.ndim != 2 or distance.shape[0] != distance.shape[1] or len(distance) < 3:
        raise ValueError("Expected a square distance matrix with at least three samples")
    if not np.isfinite(distance).all() or np.any(distance < 0):
        raise ValueError("Distances must be finite and nonnegative")
    condensed = squareform(distance, checks=True)
    tree = linkage(condensed, method="average")
    cuts, scores = {}, {}
    for k in sorted(set(candidate_k)):
        if not 2 <= k < len(distance):
            continue
        labels = fcluster(tree, k, criterion="maxclust")
        if len(np.unique(labels)) == k:
            cuts[k] = labels
            scores[k] = float(silhouette_values(distance, labels).mean())
    if not scores:
        raise ValueError("No candidate produces the requested number of clusters; inspect tied heights")
    # 最大平均轮廓系数；并列时选较小k / Highest mean silhouette, smaller k breaks ties.
    best_k = max(scores, key=lambda k: (scores[k], -k))
    selected = best_k if manual_k is None else manual_k
    if selected not in cuts:
        raise ValueError(f"Selected k must be one of {sorted(cuts)}")
    merges = len(distance) - selected
    lower, upper = tree[merges - 1, 2], tree[merges, 2]
    if not lower < upper:
        raise ValueError("A single cut height cannot represent this tied-height partition")
    height = float((lower + upper) / 2)
    # 树的显示切线必须重现相同成员关系 / Verify that the plotted cut reproduces memberships.
    check = fcluster(tree, height, criterion="distance")
    labels = cuts[selected]
    if not np.array_equal(check[:, None] == check, labels[:, None] == labels):
        raise RuntimeError("Cut-line partition and selected memberships disagree")
    correlation = float(cophenet(tree, condensed)[0])
    return HCAResult(tree, labels, silhouette_values(distance, labels), scores, cuts,
                     best_k, selected, height, correlation)
