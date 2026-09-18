"""
Run the whole pipeline in order.

    python scripts/run_all.py           all six steps
    python scripts/run_all.py 3 4 5     only steps 3, 4 and 5

Only step 1 needs internet access. Everything after it reads from the
cached files step 1 wrote, so re-running steps 2 onward is fast and works
offline.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

STEPS = [
    ("1", "run_01_fetch_data.py", "fetch every input from the World Bank API"),
    ("2", "run_02_build_indicators.py", "build the cross-sectional table, handle missingness"),
    ("3", "run_03_build_index.py", "normalise, build the composite EVI and the PCA alternative"),
    ("4", "run_04_benchmark_validate.py", "compare against the real UN LDC list"),
    ("5", "run_05_robustness.py", "weighting, jackknife and missingness-threshold checks"),
    ("6", "run_06_report.py", "generate the final report from the saved outputs"),
]


def main() -> None:
    wanted = set(sys.argv[1:]) or {s[0] for s in STEPS}
    for num, script, description in STEPS:
        if num not in wanted:
            continue
        print(f"\n########## step {num}: {script} - {description}")
        start = time.time()
        result = subprocess.run([sys.executable, str(HERE / script)])
        if result.returncode != 0:
            print(f"step {num} failed, stopping here")
            raise SystemExit(result.returncode)
        print(f"########## step {num} done in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
