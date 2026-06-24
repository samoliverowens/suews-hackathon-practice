# Physical-parameter experiments

This page records a first one-factor sensitivity screen using only physical SUEWS parameters. Each experiment changes the same parameter across all 10 UDA-city neighbourhoods and uses the future hot-humid forcing.

The response metric is the change in annual dangerous-heat hours relative to the baseline future run, where a dangerous-heat hour is an hourly mean 2 m air temperature above 35 C after the 14-day spin-up.

## Experiments

| Experiment | SUEWS parameter changed | Mean change in dangerous-heat hours | Range across sites | Fuzhou Lanes | Mlima Moto | Kampong Lama | Dhobi Lines |
|---|---:|---:|---:|---:|---:|---:|---:|
| `trees_5pp_from_paved` | +0.05 evergreen tree surface fraction, -0.05 paved fraction | +68.0 | +6 to +228 | +228 | +190 | +19 | +12 |
| `trees_10pp_from_paved` | +0.10 evergreen tree surface fraction, -0.10 paved fraction | +137.1 | +19 to +352 | +352 | +320 | +162 | +178 |
| `paved_albedo_035` | paved albedo set to 0.35 | -8.7 | -17 to -1 | -17 | -11 | -15 | -12 |
| `building_albedo_035` | building albedo set to 0.35 | -4.5 | -12 to 0 | -12 | -8 | -4 | -5 |

## Interpretation

The clearest beneficial single-factor result is raising paved-surface albedo. It reduces dangerous-heat hours in every neighbourhood, with the largest reductions in the highest-hazard sites: Fuzhou Lanes, Kampong Lama, Dhobi Lines and Mlima Moto.

Raising building albedo is also beneficial, but weaker in this setup. It reduces dangerous-heat hours by up to 12 hours and has no effect in one lower-risk site.

The simple tree-cover experiment worsens the air-temperature threshold metric in this compatibility run. That should not be read as a general conclusion that trees increase heat risk. It means this particular parameter-only edit, with no accompanying changes to irrigation, soil moisture, canopy shading geometry, or morphology, shifts the SUEWS energy balance in a way that increases near-surface air-temperature hours above 35 C. Before making a design recommendation about trees, this result needs a better vegetation scenario that also tests hydrology and canopy assumptions.

## Files

- Experiment runner: `analysis/experiments/run_physical_experiments.py`
- Combined summary: `analysis/experiments/outputs/physical_experiments_future_summary.csv`
- Experiment configs: `analysis/experiments/configs/`

## Caveat

These runs use the same local compatibility path as the baseline report: SuPy 2025.7.6 with a compatibility config, because this macOS 14 host could not install the available SuPy 2026.6.5 macOS 15 ARM wheel required by the supplied dataset.
