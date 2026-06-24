"""Run UDA-city with the local SuPy 2025 compatibility path.

The UDA-city dataset asks for SuPy >= 2026.6.5. On this macOS 14 host, pip
cannot install the available macOS 15 wheel, so this script keeps the official
dataset untouched and uses a clearly labelled compatibility YAML plus a small
forcing-reader shim for the older SuPy/pandas combination.
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import supy
from supy._load import load_SUEWS_Forcing_met_df_pattern, resample_forcing_met
from supy._run import run_supy_ser
from supy.suews_sim import SUEWSSimulation


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "uda-city-hackathon"
OUT_DIR = ROOT / "analysis" / "focus_city" / "outputs"
CONFIG = DATASET / "uda-city-supy2025-compat.yml"
PRESENT_FORCING = DATASET / "forcing" / "present_hot_humid" / "UDA_2024_data_60.txt"
FUTURE_FORCING = DATASET / "forcing" / "future_hot_humid" / "UDA_2024_data_60.txt"


def read_forcing_compat(path: Path, tstep_mod: int = 300) -> pd.DataFrame:
    """Equivalent to old ``supy.util._io.read_forcing`` with iloc indexing."""
    raw = load_SUEWS_Forcing_met_df_pattern(path.parent, path.name)
    tstep_met_in = raw.index.to_series().diff().iloc[-1] / pd.Timedelta("1s")
    raw = raw.asfreq(f"{tstep_met_in:.0f}s")
    if tstep_mod is not None and tstep_mod < tstep_met_in:
        forcing = raw.replace(-999, np.nan)
        forcing = resample_forcing_met(forcing, tstep_met_in, tstep_mod, kdownzen=0)
        return forcing.replace(np.nan, -999)
    return raw


def run_scenario(name: str, forcing_path: Path, full: bool = True) -> pd.DataFrame:
    sim = SUEWSSimulation(str(CONFIG))
    forcing = read_forcing_compat(forcing_path)
    if not full:
        forcing = forcing.head(2016)
    run_return = run_supy_ser(forcing, sim._df_state_init)
    if not isinstance(run_return, tuple) or len(run_return) < 2:
        raise RuntimeError(f"{name} returned an unexpected run payload")

    results, _state_final = run_return[:2]
    bad = []
    for grid in results.index.get_level_values(0).unique():
        suews = results.loc[grid]["SUEWS"]
        for col in ("T2", "QH"):
            if suews[col].isna().any():
                bad.append(f"grid {grid} {col}")
    if bad:
        raise RuntimeError(f"{name} has non-finite diagnostics: {', '.join(bad)}")

    return results


def summarise_results(name: str, results: pd.DataFrame) -> dict[str, object]:
    rows = []
    for grid in results.index.get_level_values(0).unique():
        suews = results.loc[grid]["SUEWS"]
        hourly_t2 = suews["T2"].iloc[14 * 288 :].resample("h").mean()
        rows.append(
            {
                "scenario": name,
                "gridiv": int(grid),
                "dangerous_heat_hours_gt35": int((hourly_t2 > 35.0).sum()),
                "t2_min_c": float(suews["T2"].min()),
                "t2_mean_c": float(suews["T2"].mean()),
                "t2_max_c": float(suews["T2"].max()),
                "qh_mean_w_m2": float(suews["QH"].mean()),
                "qe_mean_w_m2": float(suews["QE"].mean()),
                "qn_mean_w_m2": float(suews["QN"].mean()),
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DIR / f"hazard_{name}.csv", index=False)
    return {
        "scenario": name,
        "rows": int(len(results)),
        "sites": int(len(rows)),
        "dangerous_heat_hours_gt35_min": int(summary["dangerous_heat_hours_gt35"].min()),
        "dangerous_heat_hours_gt35_max": int(summary["dangerous_heat_hours_gt35"].max()),
        "t2_mean_c_min": float(summary["t2_mean_c"].min()),
        "t2_mean_c_max": float(summary["t2_mean_c"].max()),
    }


def main() -> int:
    warnings.simplefilter("ignore")
    logging.getLogger("SuPy").setLevel(logging.ERROR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    run_log: dict[str, object] = {
        "status": "started",
        "supy_version": getattr(supy, "__version__", "unknown"),
        "config": str(CONFIG.relative_to(ROOT)),
        "compatibility_notes": [
            "Official dataset requires supy >= 2026.6.5.",
            "This host is macOS 14; available supy 2026.6.5 arm64 wheel is tagged macOS 15.",
            "Compatibility config changes are recorded in analysis/focus_city/compat_changes.txt.",
            "Forcing reader uses iloc[-1] to avoid an old pandas positional-indexing bug.",
        ],
    }

    try:
        present = run_scenario("present", PRESENT_FORCING)
        future = run_scenario("future", FUTURE_FORCING)
        present.to_parquet(OUT_DIR / "suews_present.parquet")
        future.to_parquet(OUT_DIR / "suews_future.parquet")
        run_log["present"] = summarise_results("present", present)
        run_log["future"] = summarise_results("future", future)
        run_log["status"] = "success"
    except Exception as exc:  # noqa: BLE001 - log full failure for transcript.
        run_log["status"] = "failed"
        run_log["error"] = repr(exc)
        run_log["traceback"] = traceback.format_exc()
        (OUT_DIR / "run_summary.json").write_text(
            json.dumps(run_log, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(run_log, indent=2))
        return 1

    (OUT_DIR / "run_summary.json").write_text(
        json.dumps(run_log, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(run_log, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
