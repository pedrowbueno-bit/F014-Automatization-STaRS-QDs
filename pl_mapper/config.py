# -*- coding: utf-8 -*-
"""
Scan configuration — all parameters for a 2D PL mapping run.

Centralises every tuneable knob so that the scanning logic
(scanner.py) stays free of magic numbers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

import numpy as np


@dataclass
class ScanConfig:
    """Immutable-ish bag of parameters for one scan run.

    Units
    -----
    Positions are in whatever unit the motor controller expects
    (typically µm or nm).  Times are in seconds.
    """

    # --- spatial grid --------------------------------------------------
    x_start: float = 2.0
    x_end: float = 10.0
    x_step: float = 2.0

    y_start: float = 2.0
    y_end: float = 10.0
    y_step: float = 2.0

    # --- timing --------------------------------------------------------
    motor_settle_s: float = 0.5    # wait after each motor command
    detector_settle_s: float = 0.5  # wait after each detector read

    # --- output --------------------------------------------------------
    output_dir: Path = field(default_factory=lambda: Path("data"))
    filename_prefix: str = "scan"

    # --- VISA addresses (empty → auto-detect) --------------------------
    motor_visa_addr: str = ""
    detector_visa_addr: str = ""

    # ------------------------------------------------------------------
    # Derived helpers (not stored, computed on the fly)
    # ------------------------------------------------------------------

    @property
    def xs(self) -> np.ndarray:
        """X positions including the endpoint."""
        return np.arange(
            self.x_start,
            self.x_end + self.x_step / 2,
            self.x_step,
        )

    @property
    def ys(self) -> np.ndarray:
        """Y positions including the endpoint."""
        return np.arange(
            self.y_start,
            self.y_end + self.y_step / 2,
            self.y_step,
        )

    @property
    def n_points(self) -> int:
        return len(self.xs) * len(self.ys)

    @property
    def grid_shape(self) -> tuple[int, int]:
        """(n_rows, n_cols) i.e. (ny, nx)."""
        return len(self.ys), len(self.xs)

    def output_path(self, ext: str = ".csv") -> Path:
        """Timestamped output file path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{self.filename_prefix}_{ts}{ext}"

    def __post_init__(self) -> None:
        if self.x_step <= 0 or self.y_step <= 0:
            raise ValueError("Step sizes must be positive.")
        if self.x_end < self.x_start or self.y_end < self.y_start:
            raise ValueError("End position must be >= start position.")
