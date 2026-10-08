"""NVPD 全量主实验的公共函数接口。

Public functions for the primary NVPD global comparison workflow.
"""
from .config import Config
from .data import Sample, load_samples, bundled_data_dir
from .preprocessing import voxel_downsample, estimate_normals, orient_normals
from .representation import spherical_angles, normal_distribution, align_facade_peak, smooth_azimuth
from .analysis import js_distance_matrix, silhouette_values, average_hca, HCAResult
from .contributions import distance_contribution, cluster_profiles
from .pipeline import Representations, build_representations, export_results, run_global
from .modules import (Stage, preprocess, compute_nvpd, align_nvpd, smooth_nvpd,
                      compute_distances, cluster_hca, compare_clusters, save_results)

__version__ = "0.1.0"
__all__ = ["Config", "Sample", "load_samples", "bundled_data_dir", "voxel_downsample", "estimate_normals", "orient_normals",
           "spherical_angles", "normal_distribution", "align_facade_peak", "smooth_azimuth",
           "js_distance_matrix", "silhouette_values", "average_hca", "HCAResult", "distance_contribution",
           "cluster_profiles", "Representations", "build_representations", "export_results", "run_global",
           "Stage", "preprocess", "compute_nvpd", "align_nvpd", "smooth_nvpd",
           "compute_distances", "cluster_hca", "compare_clusters", "save_results"]
