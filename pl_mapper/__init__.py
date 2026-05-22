# -*- coding: utf-8 -*-
"""
pl_mapper — 2-D photoluminescence mapping via PyVISA.

Quickstart
----------
>>> from pl_mapper import ScanConfig, create_instruments, run_scan, plot_heatmap
>>> cfg = ScanConfig(x_start=0, x_end=20, x_step=2,
...                  y_start=0, y_end=20, y_step=2)
>>> motor, detector = create_instruments(cfg, simulate=True)
>>> df = run_scan(cfg, motor, detector)
>>> plot_heatmap(df, cfg, cmap="viridis")
"""

from .config import ScanConfig
from .scanner import (
    create_instruments,
    run_scan,
    Motor,
    Detector,
    SimulatedMotor,
    SimulatedDetector,
    VisaMotor,
    VisaDetector,
)
from .plotter import plot_heatmap

__all__ = [
    "ScanConfig",
    "create_instruments",
    "run_scan",
    "plot_heatmap",
    "Motor",
    "Detector",
    "SimulatedMotor",
    "SimulatedDetector",
    "VisaMotor",
    "VisaDetector",
]

__version__ = "1.0.0"
