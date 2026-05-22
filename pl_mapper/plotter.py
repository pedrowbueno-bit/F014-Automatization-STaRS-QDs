# -*- coding: utf-8 -*-
"""
Visualisation utilities for 2-D PL intensity maps.

The main entry point is :func:`plot_heatmap`, which takes the scan
DataFrame and produces an annotated heatmap with a colour bar.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from .config import ScanConfig


# ── Public API ──────────────────────────────────────────────────────

def plot_heatmap(
    df: pd.DataFrame,
    cfg: ScanConfig,
    *,
    cmap: str = "viridis",
    annotate: bool = True,
    save_path: Path | str | None = None,
    show: bool = True,
) -> plt.Figure:
    """Build an annotated 2-D heatmap from scan data.

    Parameters
    ----------
    df : DataFrame
        Must contain columns ``intensity``, ``x``, ``y``.
    cfg : ScanConfig
        Used to reconstruct the grid dimensions.
    cmap : str
        Any Matplotlib colourmap name.
    annotate : bool
        Whether to print numeric values inside each cell.
    save_path : Path or str, optional
        If given, save the figure (PNG 150 dpi).
    show : bool
        Call ``plt.show()`` at the end.

    Returns
    -------
    matplotlib.figure.Figure
    """
    ny, nx = cfg.grid_shape
    xs_sorted = np.sort(df["x"].unique())
    ys_sorted = np.sort(df["y"].unique())

    # Build 2-D intensity matrix
    matrix = np.zeros((ny, nx))
    for _, row in df.iterrows():
        ix = int(np.searchsorted(xs_sorted, row["x"]))
        iy = int(np.searchsorted(ys_sorted, row["y"]))
        matrix[iy, ix] = row["intensity"]

    x_labels = [f"{v:.0f}" for v in xs_sorted]
    y_labels = [f"{v:.0f}" for v in ys_sorted]

    fig, ax = plt.subplots(figsize=(max(2 * nx, 6), max(2 * ny, 5)))

    im = ax.imshow(matrix, cmap=cmap, aspect="equal")
    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Intensity [PL]", rotation=-90, va="bottom")

    # Tick labels
    ax.set_xticks(np.arange(nx))
    ax.set_xticklabels(x_labels)
    ax.set_yticks(np.arange(ny))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("x position")
    ax.set_ylabel("y position")
    ax.set_title("2-D Photoluminescence Map")

    # Grid
    ax.set_xticks(np.arange(nx + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(ny + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="w", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    if annotate:
        _annotate_cells(im, matrix)

    fig.tight_layout()

    if save_path is not None:
        fig.savefig(str(save_path), dpi=150, bbox_inches="tight")
        print(f"✓ Heatmap saved to {save_path}")

    if show:
        plt.show()

    return fig


# ── Internals ───────────────────────────────────────────────────────

def _annotate_cells(
    im,
    data: np.ndarray,
    fmt: str = "{x:.3f}",
    textcolors: tuple[str, str] = ("black", "white"),
) -> list:
    """Write numeric labels inside each heatmap cell."""
    threshold = im.norm(data.max()) / 2.0
    formatter = mticker.StrMethodFormatter(fmt)
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            color = textcolors[int(im.norm(data[i, j]) > threshold)]
            t = im.axes.text(
                j, i, formatter(data[i, j], None),
                ha="center", va="center", color=color, fontsize=9,
            )
            texts.append(t)
    return texts
