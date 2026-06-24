"""Run one-factor physical-parameter SUEWS experiments for UDA-city.

The experiments deliberately change only SUEWS physical inputs:

* tree cover fraction, balanced by paved fraction
* paved-surface albedo
* building-surface albedo

They run against the future hot-humid forcing only and save compact CSVs, not
large parquet result frames.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import warnings
from pathlib import Path

import pandas as pd
import supy
import yaml
from supy._run import run_supy_ser
from supy.suews_sim import SUEWSSimulation


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "uda-city-hackathon"
BASE_CONFIG = ROOT / "analysis" / "focus_city" / "uda-city-supy2025-compat.yml"
CONFIG_DIR = ROOT / "analysis" / "experiments" / "configs"
OUT_DIR = ROOT / "analysis" / "experiments" / "outputs"
FUTURE_FORCING = DATASET / "forcing" / "future_hot_humid" / "UDA_2024_data_60.txt"
BASELINE_FUTURE_RISK = ROOT / "analysis" / "focus_city" / "outputs" / "risk_future.csv"


sys.path.insert(0, str(ROOT / "analysis" / "focus_city"))
sys.path.insert(0, str(DATASET))

from run_focus_city_compat import read_forcing_compat  # noqa: E402
from risk_bridge import build_risk, load_neighbourhoods  # noqa: E402


EXPERIMENTS = [
    {
        "name": "trees_5pp_from_paved",
        "description": "Add 5 percentage points evergreen tree cover, removing the same amount from paved cover.",
        "operation": "tree_from_paved",
        "delta": 0.05,
    },
    {
        "name": "trees_10pp_from_paved",
        "description": "Add 10 percentage points evergreen tree cover, removing the same amount from paved cover.",
        "operation": "tree_from_paved",
        "delta": 0.10,
    },
    {
        "name": "paved_albedo_035",
        "description": "Raise paved-surface albedo to 0.35.",
        "operation": "surface_albedo",
        "surface": "paved",
        "albedo": 0.35,
    },
    {
        "name": "building_albedo_035",
        "description": "Raise building-surface albedo to 0.35.",
        "operation": "surface_albedo",
        "surface": "bldgs",
        "albedo": 0.35,
    },
]


def land_cover(site: dict) -> dict:
    return site["properties"]["land_cover"]


def value(node: dict) -> float:
    return float(node["value"])


def set_value(node: dict, new_value: float) -> None:
    node["value"] = round(float(new_value), 6)


def validate_land_cover(site: dict) -> None:
    cover = land_cover(site)
    surfaces = ("paved", "bldgs", "evetr", "dectr", "grass", "bsoil", "water")
    total = sum(value(cover[surface]["sfr"]) for surface in surfaces)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"{site['name']} land-cover fractions sum to {total:.8f}")
    for surface in surfaces:
        sfr = value(cover[surface]["sfr"])
        if sfr < -1e-9:
            raise ValueError(f"{site['name']} has negative {surface} fraction: {sfr}")


def apply_experiment(config: dict, experiment: dict) -> list[dict]:
    changes = []
    for site in config["sites"]:
        cover = land_cover(site)
        if experiment["operation"] == "tree_from_paved":
            delta = float(experiment["delta"])
            paved = value(cover["paved"]["sfr"])
            evetr = value(cover["evetr"]["sfr"])
            if paved < delta:
                raise ValueError(f"{site['name']} has paved fraction {paved}, cannot remove {delta}")
            set_value(cover["paved"]["sfr"], paved - delta)
            set_value(cover["evetr"]["sfr"], evetr + delta)
            changes.append(
                {
                    "gridiv": site["gridiv"],
                    "name": site["name"],
                    "paved_sfr_before": paved,
                    "paved_sfr_after": paved - delta,
                    "evetr_sfr_before": evetr,
                    "evetr_sfr_after": evetr + delta,
                }
            )
        elif experiment["operation"] == "surface_albedo":
            surface = experiment["surface"]
            before = value(cover[surface]["alb"])
            after = float(experiment["albedo"])
            set_value(cover[surface]["alb"], after)
            changes.append(
                {
                    "gridiv": site["gridiv"],
                    "name": site["name"],
                    f"{surface}_albedo_before": before,
                    f"{surface}_albedo_after": after,
                }
            )
        else:
            raise ValueError(f"Unknown operation: {experiment['operation']}")
        validate_land_cover(site)
    return changes


def write_config(experiment: dict) -> tuple[Path, list[dict]]:
    config = yaml.safe_load(BASE_CONFIG.read_text(encoding="utf-8"))
    changes = apply_experiment(config, experiment)
    path = CONFIG_DIR / f"{experiment['name']}.yml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path, changes


def run_config(config_path: Path) -> pd.DataFrame:
    sim = SUEWSSimulation(str(config_path))
    forcing = read_forcing_compat(FUTURE_FORCING)
    results, _state_final = run_supy_ser(forcing, sim._df_state_init)[:2]
    return results


def summarise_energy(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for grid in results.index.get_level_values(0).unique():
        suews = results.loc[grid]["SUEWS"]
        rows.append(
            {
                "gridiv": int(grid),
                "t2_mean_c": float(suews["T2"].mean()),
                "t2_max_c": float(suews["T2"].max()),
                "qh_mean_w_m2": float(suews["QH"].mean()),
                "qe_mean_w_m2": float(suews["QE"].mean()),
                "qn_mean_w_m2": float(suews["QN"].mean()),
                "qs_mean_w_m2": float(suews["QS"].mean()),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    warnings.simplefilter("ignore")
    logging.getLogger("SuPy").setLevel(logging.ERROR)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_FUTURE_RISK)
    baseline = baseline[["gridiv", "dangerous_heat_hours", "risk_index", "risk_rank"]].rename(
        columns={
            "dangerous_heat_hours": "baseline_dangerous_heat_hours",
            "risk_index": "baseline_risk_index",
            "risk_rank": "baseline_risk_rank",
        }
    )
    neighbourhoods = load_neighbourhoods(DATASET / "neighbourhoods.yml")
    socio = pd.read_csv(DATASET / "socioeconomic.csv")

    all_summary = []
    run_log = {
        "status": "started",
        "supy_version": getattr(supy, "__version__", "unknown"),
        "future_forcing": str(FUTURE_FORCING.relative_to(ROOT)),
        "experiments": [],
    }

    for experiment in EXPERIMENTS:
        started = time.perf_counter()
        config_path, changes = write_config(experiment)
        results = run_config(config_path)
        risk = build_risk(results, neighbourhoods, socio)
        energy = summarise_energy(results)
        summary = risk.merge(energy, on="gridiv", how="left").merge(baseline, on="gridiv", how="left")
        summary["experiment"] = experiment["name"]
        summary["delta_dangerous_heat_hours"] = (
            summary["dangerous_heat_hours"] - summary["baseline_dangerous_heat_hours"]
        )
        summary["delta_risk_index"] = summary["risk_index"] - summary["baseline_risk_index"]
        cols = [
            "experiment",
            "gridiv",
            "name",
            "type",
            "dangerous_heat_hours",
            "baseline_dangerous_heat_hours",
            "delta_dangerous_heat_hours",
            "risk_index",
            "baseline_risk_index",
            "delta_risk_index",
            "risk_rank",
            "baseline_risk_rank",
            "t2_mean_c",
            "t2_max_c",
            "qh_mean_w_m2",
            "qe_mean_w_m2",
            "qn_mean_w_m2",
            "qs_mean_w_m2",
        ]
        summary = summary[cols].sort_values(["experiment", "gridiv"])
        summary.to_csv(OUT_DIR / f"{experiment['name']}_future_summary.csv", index=False)
        pd.DataFrame(changes).to_csv(OUT_DIR / f"{experiment['name']}_changes.csv", index=False)
        all_summary.append(summary)
        run_log["experiments"].append(
            {
                "name": experiment["name"],
                "description": experiment["description"],
                "config": str(config_path.relative_to(ROOT)),
                "elapsed_seconds": round(time.perf_counter() - started, 1),
                "min_delta_dangerous_heat_hours": int(summary["delta_dangerous_heat_hours"].min()),
                "max_delta_dangerous_heat_hours": int(summary["delta_dangerous_heat_hours"].max()),
            }
        )
        print(json.dumps(run_log["experiments"][-1], indent=2))

    combined = pd.concat(all_summary, ignore_index=True)
    combined.to_csv(OUT_DIR / "physical_experiments_future_summary.csv", index=False)
    run_log["status"] = "success"
    (OUT_DIR / "physical_experiments_run_summary.json").write_text(
        json.dumps(run_log, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(run_log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
