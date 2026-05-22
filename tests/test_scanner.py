# -*- coding: utf-8 -*-
"""Tests for pl_mapper core functionality."""

import numpy as np
import pytest

from pl_mapper import ScanConfig, create_instruments, run_scan


class TestScanConfig:
    """ScanConfig validation and derived properties."""

    def test_grid_dimensions(self):
        cfg = ScanConfig(x_start=0, x_end=10, x_step=2,
                         y_start=0, y_end=6, y_step=3)
        assert cfg.grid_shape == (3, 6)  # ny=3, nx=6
        assert cfg.n_points == 18

    def test_xs_includes_endpoint(self):
        cfg = ScanConfig(x_start=2, x_end=10, x_step=2)
        np.testing.assert_array_equal(cfg.xs, [2, 4, 6, 8, 10])

    def test_negative_step_raises(self):
        with pytest.raises(ValueError, match="positive"):
            ScanConfig(x_step=-1)

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError, match=">="):
            ScanConfig(x_start=10, x_end=2)


class TestSerpentineScan:
    """Verify the serpentine acquisition pattern."""

    @pytest.fixture
    def small_scan(self):
        cfg = ScanConfig(
            x_start=0, x_end=4, x_step=2,
            y_start=0, y_end=4, y_step=2,
        )
        motor, detector = create_instruments(cfg, simulate=True)
        df = run_scan(cfg, motor, detector, verbose=False)
        return cfg, df

    def test_total_points(self, small_scan):
        cfg, df = small_scan
        assert len(df) == cfg.n_points

    def test_columns_present(self, small_scan):
        _, df = small_scan
        assert set(df.columns) == {"intensity", "x", "y", "elapsed_s"}

    def test_serpentine_x_direction(self, small_scan):
        _, df = small_scan
        # Row 0 (y=0): x should go 0 → 2 → 4
        row0 = df[df["y"] == 0]["x"].values
        assert list(row0) == [0, 2, 4]

        # Row 1 (y=2): x should go 4 → 2 → 0 (reversed)
        row1 = df[df["y"] == 2]["x"].values
        assert list(row1) == [4, 2, 0]

        # Row 2 (y=4): x should go 0 → 2 → 4 again
        row2 = df[df["y"] == 4]["x"].values
        assert list(row2) == [0, 2, 4]

    def test_intensities_are_finite(self, small_scan):
        _, df = small_scan
        assert df["intensity"].notna().all()
        assert np.isfinite(df["intensity"].values).all()

    def test_csv_output_created(self, small_scan, tmp_path):
        cfg = ScanConfig(
            x_start=0, x_end=2, x_step=1,
            y_start=0, y_end=2, y_step=1,
            output_dir=tmp_path,
        )
        motor, det = create_instruments(cfg, simulate=True)
        run_scan(cfg, motor, det, verbose=False)
        csvs = list(tmp_path.glob("*.csv"))
        assert len(csvs) == 1
