"""可选命令行入口；默认 notebook 无需此操作。

Optional command-line entry point; not required for the default notebook.
"""
import argparse
import json
from .config import Config
from .data import load_samples
from .pipeline import run_global


def main(argv=None):
    parser = argparse.ArgumentParser(description="NVPD global comparison: align, smooth, sqrt-JSD, average HCA")
    parser.add_argument("--input", required=True, help="Directory of OBJ, point-cloud, or prepared NPY files")
    parser.add_argument("--input-mode", choices=["obj", "raw_points", "voxel_points", "prepared"], default="voxel_points")
    parser.add_argument("--samples", help="Optional CSV sample catalog with sample and sample_id columns")
    parser.add_argument("--voxel-coefficient", type=float, required=True,
                        help="Voxel side / original height: 0.025 for public demonstration, 0.009 for paper replication")
    parser.add_argument("--normal-k", type=int, default=7, help="PCA neighbors INCLUDING the query point (default 7)")
    parser.add_argument("--manual-k", type=int, help="Override silhouette-selected k with a valid cut in 2..8")
    parser.add_argument("--output", required=True, help="New or empty result directory")
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--no-individual-images", action="store_true", help="Keep atlases but omit per-sample PNGs")
    parser.add_argument("--export-point-arrays", action="store_true", help="Also copy point and normal arrays to results")
    args = parser.parse_args(argv)
    import matplotlib
    matplotlib.use("Agg")
    config = Config(voxel_coefficient=args.voxel_coefficient, normal_k=args.normal_k, manual_k=args.manual_k)
    samples = load_samples(args.input, args.input_mode, config, args.samples)
    result = run_global(samples, args.output, config, make_plots=not args.no_figures,
                        individual_images=not args.no_individual_images, save_point_arrays=args.export_point_arrays)
    print(json.dumps({"samples": len(samples), "best_k": result["hca"].best_k,
                      "selected_k": result["hca"].selected_k,
                      "mean_silhouette": float(result["hca"].silhouette.mean()),
                      "output": str(result["output"].resolve())}, indent=2))


if __name__ == "__main__":
    main()
