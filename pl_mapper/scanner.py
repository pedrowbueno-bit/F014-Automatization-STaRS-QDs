# -*- coding: utf-8 -*-
"""
2-D serpentine scanner — the core acquisition loop.

Supports two backends:
  • **hardware** — real PyVISA communication with motor + detector
  • **simulated** — random intensities for offline development / CI

The serpentine (boustrophedon) pattern alternates the x-sweep
direction on every row, eliminating the backlash error that would
accumulate if the motor always returned to x_start.

    Row 0  →  →  →  →  →
    Row 1  ←  ←  ←  ←  ←
    Row 2  →  →  →  →  →
    ...
"""

from __future__ import annotations

import time
from typing import Protocol

import numpy as np
import pandas as pd

from .config import ScanConfig


# ── Abstract instrument interfaces ──────────────────────────────────

class Motor(Protocol):
    """Anything that can move to a position and confirm arrival."""

    def move(self, axis: str, position: float) -> None: ...
    def query_position(self, axis: str) -> float: ...


class Detector(Protocol):
    """Anything that returns a scalar intensity reading."""

    def read_intensity(self) -> float: ...


# ── Hardware (real VISA) implementations ────────────────────────────

class VisaMotor:
    """Newport-style motor controlled via PyVISA SCPI commands.

    Parameters
    ----------
    resource : pyvisa.Resource
        Already-opened VISA resource handle.
    settle_s : float
        Seconds to wait after issuing a move command.
    """

    # Map logical axis names to SCPI axis identifiers.
    # Adjust these to match your actual controller.
    AXIS_MAP = {"x": "1", "y": "2"}

    def __init__(self, resource, settle_s: float = 0.5) -> None:
        self._res = resource
        self._settle = settle_s

    def move(self, axis: str, position: float) -> None:
        ax = self.AXIS_MAP[axis]
        self._res.write(f"{ax}PA{position}")
        time.sleep(self._settle)

    def query_position(self, axis: str) -> float:
        ax = self.AXIS_MAP[axis]
        resp = self._res.query(f"{ax}TP?")
        return float(resp)


class VisaDetector:
    """Generic SCPI detector (e.g. Horiba iHR 320).

    Parameters
    ----------
    resource : pyvisa.Resource
        Already-opened VISA resource handle.
    settle_s : float
        Seconds to wait after each measurement.
    """

    def __init__(self, resource, settle_s: float = 0.5) -> None:
        self._res = resource
        self._settle = settle_s

    def read_intensity(self) -> float:
        resp = self._res.query("MEAS?")
        time.sleep(self._settle)
        return float(resp)


# ── Simulated (offline) implementations ─────────────────────────────

class SimulatedMotor:
    """In-memory motor that just tracks position."""

    def __init__(self) -> None:
        self._pos: dict[str, float] = {"x": 0.0, "y": 0.0}

    def move(self, axis: str, position: float) -> None:
        self._pos[axis] = position

    def query_position(self, axis: str) -> float:
        return self._pos[axis]


class SimulatedDetector:
    """Returns random intensities for testing."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = np.random.default_rng(seed)

    def read_intensity(self) -> float:
        return float(self._rng.random())


# ── Factory ─────────────────────────────────────────────────────────

def create_instruments(
    cfg: ScanConfig,
    simulate: bool = False,
) -> tuple[Motor, Detector]:
    """Return a (motor, detector) pair.

    Parameters
    ----------
    cfg : ScanConfig
    simulate : bool
        If *True*, return simulated instruments (no hardware needed).
    """
    if simulate:
        return SimulatedMotor(), SimulatedDetector()

    try:
        import pyvisa as visa
    except ImportError as exc:
        raise ImportError(
            "PyVISA is required for hardware mode.  "
            "Install it with:  pip install pyvisa pyvisa-py"
        ) from exc

    rm = visa.ResourceManager()
    resources = rm.list_resources()
    if len(resources) < 2:
        raise RuntimeError(
            f"Expected ≥ 2 VISA resources, found {len(resources)}: {resources}"
        )

    motor_addr = cfg.motor_visa_addr or resources[0]
    det_addr = cfg.detector_visa_addr or resources[1]

    motor = VisaMotor(
        rm.open_resource(motor_addr),
        settle_s=cfg.motor_settle_s,
    )
    detector = VisaDetector(
        rm.open_resource(det_addr),
        settle_s=cfg.detector_settle_s,
    )
    return motor, detector


# ── Core scan routine ───────────────────────────────────────────────

def run_scan(
    cfg: ScanConfig,
    motor: Motor,
    detector: Detector,
    *,
    verbose: bool = True,
) -> pd.DataFrame:
    """Execute a full 2-D serpentine scan.

    Returns a DataFrame with columns:
        Intensity, x, y, elapsed_s
    """
    xs, ys = cfg.xs, cfg.ys
    records: list[list[float]] = []
    t0 = time.time()

    for iy, yval in enumerate(ys):
        motor.move("y", float(yval))

        # Serpentine: even rows left→right, odd rows right→left
        x_sweep = xs if iy % 2 == 0 else xs[::-1]

        for xval in x_sweep:
            motor.move("x", float(xval))
            intensity = detector.read_intensity()
            elapsed = time.time() - t0
            records.append([intensity, float(xval), float(yval), elapsed])

            if verbose:
                print(
                    f"  ({xval:7.2f}, {yval:7.2f}) → I = {intensity:.6f}  "
                    f"[t = {elapsed:.1f} s]"
                )

    df = pd.DataFrame(records, columns=["intensity", "x", "y", "elapsed_s"])

    # Persist
    out = cfg.output_path(".csv")
    df.to_csv(out, index=False)
    if verbose:
        print(f"\n✓ {len(df)} points saved to {out}")

    return df
