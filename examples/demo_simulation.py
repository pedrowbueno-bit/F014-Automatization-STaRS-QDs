#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick demo — run a simulated 5×5 scan and plot the heatmap.

    python examples/demo_simulation.py
"""

from pl_mapper import ScanConfig, create_instruments, run_scan, plot_heatmap


def main():
    cfg = ScanConfig(
        x_start=0, x_end=40, x_step=10,
        y_start=0, y_end=40, y_step=10,
        output_dir="data",
    )

    print(f"Running simulated {cfg.grid_shape[1]}×{cfg.grid_shape[0]} scan "
          f"({cfg.n_points} points)\n")

    motor, detector = create_instruments(cfg, simulate=True)
    df = run_scan(cfg, motor, detector)

    print(f"\nDataFrame preview:\n{df.head(10)}\n")

    plot_heatmap(
        df, cfg,
        cmap="viridis",
        save_path=cfg.output_path(".png"),
        show=True,
    )


if __name__ == "__main__":
    main()
