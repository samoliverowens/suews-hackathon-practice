"""Run a tiny SUEWS/SuPy smoke test for the hackathon practice repo."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import supy


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "smoke_outputs"
START = "2012-08-01"
END = "2012-08-02"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df_output, df_state_final = supy.run_supy_sample(
        start=START,
        end=END,
        serial_mode=True,
        logging_level=logging.WARNING,
    )

    suews = df_output["SUEWS"]
    variables = ["T2", "QN", "QH", "QE", "QS", "Rain"]
    key = suews[variables].copy()
    key.to_csv(OUT_DIR / "sample_suews_key_variables.csv")

    summary = {
        "status": "success",
        "runtime": "supy",
        "supy_version": getattr(supy, "__version__", "unknown"),
        "sample_period": {"start": START, "end": END},
        "output_shape": list(df_output.shape),
        "final_state_shape": list(df_state_final.shape),
        "first_timestamp": str(df_output.index.min()),
        "last_timestamp": str(df_output.index.max()),
        "variables_exported": variables,
        "t2_celsius": {
            "min": float(suews["T2"].min()),
            "mean": float(suews["T2"].mean()),
            "max": float(suews["T2"].max()),
        },
        "energy_flux_means_w_m2": {
            name: float(suews[name].mean()) for name in ["QN", "QH", "QE", "QS"]
        },
        "rows_with_missing_exported_values": int(key.isna().any(axis=1).sum()),
    }

    (OUT_DIR / "sample_suews_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
