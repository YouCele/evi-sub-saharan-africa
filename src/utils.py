"""Small helpers shared across the pipeline: logging, saving, checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

_WIDTH = 78


def banner(text: str) -> None:
    print("\n" + "=" * _WIDTH)
    print(text)
    print("=" * _WIDTH)


def step(text: str) -> None:
    print(f"\n-- {text}")


def note(text: str) -> None:
    print(f"   {text}")


def fail(text: str) -> None:
    print(f"\n!! BLOCKING PROBLEM: {text}", file=sys.stderr)
    raise SystemExit(1)


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    path = config.OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)
    note(f"saved {path.relative_to(config.PROJECT_ROOT)}  ({len(df)} rows)")
    return path


def save_json(obj, name: str) -> Path:
    path = config.OUTPUT_DIR / name
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, default=_json_default)
    note(f"saved {path.relative_to(config.PROJECT_ROOT)}")
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    return str(o)


def save_fig(fig, name: str) -> Path:
    path = config.FIGURE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    note(f"saved {path.relative_to(config.PROJECT_ROOT)}")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


def read_processed(name: str) -> pd.DataFrame:
    path = config.PROCESSED_DIR / name
    if not path.exists():
        fail(f"{path} not found. Run the earlier script first.")
    return pd.read_csv(path)


def write_processed(df: pd.DataFrame, name: str) -> Path:
    path = config.PROCESSED_DIR / name
    df.to_csv(path, index=False)
    note(f"saved {path.relative_to(config.PROJECT_ROOT)}  shape={df.shape}")
    return path


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"
