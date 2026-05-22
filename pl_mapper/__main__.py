#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for pl_mapper.

Usage
-----
    # Simulated scan (no hardware)
    python -m pl_mapper --simulate

    # Real hardware scan
    python -m pl_mapper --x-start 0 --x-end 50 --x-step 5 \
                        --y-start 0 --y-end 50 --y-step 5

    # Custom output and colourmap
    python -m pl_mapper --simulate --output data/ --cmap inferno
"""

import argparse
import sys

from .config import ScanConfig
from .scanner import create_instruments, run_scan
from .plotter import plot_heatmap


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="pl_mapper",
        description="2-D photoluminescence mapper with serpentine scanning.",
    )

    # Spatial grid
    p.add_argument("--x-start", type=float, default=2.0)
    p.add_argument("--x-end", type=float, default=10.0)
    p.add_argument("--x-step", type=float, default=2.0)
    p.add_argument("--y-start", type=float, default=2.0)
    p.add_argument("--y-end", type=float, default=10.0)
    p.add_argument("--y-step", type=float, default=2.0)

    # Timing
    p.add_argument("--motor-settle", type=float, default=0.5,
                    help="Seconds to wait after motor move")
    p.add_argument("--detector-settle", type=float, default=0.5,
                    help="Seconds to wait after detector read")

    # Output
    p.add_argument("--output", "-o", type=str, default="data",
                    help="Output directory for CSV and heatmap")
    p.add_argument("--cmap", type=str, default="viridis",
                    help="Matplotlib colourmap name")
    p.add_argument("--no-plot", action="store_true",
                    help="Skip heatmap generation")

    # Mode
    p.add_argument("--simulate", action="store_true",
                    help="Use simulated instruments (no hardware)")
    p.add_argument("--quiet", "-q", action="store_true",
                    help="Suppress per-point output")

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    cfg = ScanConfig(
        x_start=args.x_start,
        x_end=args.x_end,
        x_step=args.x_step,
        y_start=args.y_start,
        y_end=args.y_end,
        y_step=args.y_step,
        motor_settle_s=args.motor_settle,
        detector_settle_s=args.detector_settle,
        output_dir=__import__("pathlib").Path(args.output),
    )

    print(f"Grid: {cfg.grid_shape[1]}×{cfg.grid_shape[0]} = {cfg.n_points} points")
    print(f"Mode: {'simulated' if args.simulate else 'hardware'}")
    print()

    motor, detector = create_instruments(cfg, simulate=args.simulate)
    df = run_scan(cfg, motor, detector, verbose=not args.quiet)

    if not args.no_plot:
        heatmap_path = cfg.output_path(".png")
        plot_heatmap(df, cfg, cmap=args.cmap, save_path=heatmap_path, show=False)


if __name__ == "__main__":
    main()
