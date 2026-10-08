"""Descriptive cluster means and all-pairs angular difference contributions."""
from itertools import combinations
import numpy as np
from scipy.special import xlogy


def distance_contribution(p, q, distance):
    """中文：输入两个 NVPD 和对应的距离 d=√JSD。每格散度贡献 c 的总和为 d²；用 c/d 分配距离后总和为 d。完全相同的分布返回零矩阵。此分配是差异的角度定位，不是因果解释。

    English:
    Allocate a pair's sqrt(JSD_2) as c_bin/distance, where sum(c_bin)=distance^2.
    
    This is a documented distance-contribution allocation, not a new distance
    between individual bins. Identical distributions give all zeros. Its sum
    equals the full pair distance; it is not a causal attribution to architecture.
    """
    midpoint = (p + q) / 2
    rp = np.divide(p, midpoint, out=np.zeros_like(p), where=midpoint > 0)
    rq = np.divide(q, midpoint, out=np.zeros_like(q), where=midpoint > 0)
    # xlogy将0*log(0)安全定义为0；除以ln2得到底数2 / Zero-safe entropy terms, base 2.
    bins = (xlogy(p, rp) + xlogy(q, rq)) / (2 * np.log(2))
    if not np.isclose(bins.sum(), distance ** 2, atol=1e-10):
        raise ValueError("Distributions and supplied distance disagree")
    return bins / distance if distance > 0 else np.zeros_like(p)


def cluster_profiles(matrices, distance, labels):
    """中文：簇均值使用全部成员；簇内图平均全部无序样本对；簇间图平均两个簇全部交叉样本对。无符号图的总和等于平均距离；有符号图在每对上乘 sign(p-q)，红/正表示前一簇概率较多，蓝/负表示后一簇较多，平均可能抵消。单例簇记录 pair_count=0。

    English:
    Means, within-cluster contributions and signed/unsigned cross-cluster maps.
    
    Within: average all unordered pairs. Between: average the full Cartesian
    product of the two clusters. A positive signed bin indicates larger probability
    in the FIRST cluster, negative in the second. Signed averaging can cancel;
    only the UNSIGNED map sums to the mean cross-cluster distance. Singleton
    within maps are zero with pair_count=0, not evidence of low variation.
    """
    matrices = np.asarray(matrices, dtype=np.float64)
    distance = np.asarray(distance, dtype=np.float64)
    labels = np.asarray(labels)
    if len(labels) != len(matrices) or distance.shape != (len(labels), len(labels)):
        raise ValueError("Matrices, labels and distances must have matching sample counts")
    groups = {int(g): np.flatnonzero(labels == g) for g in np.unique(labels)}
    means, within, between = {}, {}, {}
    for group, indices in groups.items():
        # 使用全部成员，不只使用代表塔 / Use every member, not a representative subset.
        means[group] = matrices[indices].mean(axis=0)
        result = np.zeros_like(matrices[0])
        pairs = list(combinations(indices, 2))
        for i, j in pairs:
            result += distance_contribution(matrices[i], matrices[j], distance[i, j])
        if pairs:
            result /= len(pairs)
        within[group] = {"map": result, "pair_count": len(pairs)}
    for left, right in combinations(groups, 2):
        unsigned, signed = np.zeros_like(matrices[0]), np.zeros_like(matrices[0])
        for i in groups[left]:
            for j in groups[right]:
                contribution = distance_contribution(matrices[i], matrices[j], distance[i, j])
                unsigned += contribution
                # 先按每对确定方向再平均，正负可能抵消 / Sign each pair before averaging; cancellation is possible.
                signed += contribution * np.sign(matrices[i] - matrices[j])
        count = len(groups[left]) * len(groups[right])
        between[(left, right)] = {"unsigned": unsigned / count, "signed": signed / count,
            "pair_count": count, "mean_distance": float(distance[np.ix_(groups[left], groups[right])].mean())}
    return {"means": means, "within": within, "between": between}
