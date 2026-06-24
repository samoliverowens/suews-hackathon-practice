# Physical-parameter experiments

This page records a first one-factor sensitivity screen using only physical SUEWS parameters. Each experiment changes the same parameter across all 10 UDA-city neighbourhoods and uses the future hot-humid forcing.

The response metric is the change in annual dangerous-heat hours relative to the baseline future run, where a dangerous-heat hour is an hourly mean 2 m air temperature above 35 C after the 14-day spin-up.

## Experiment Summary

| Experiment | SUEWS parameter changed | Baseline mean hours | Experiment mean hours | Mean change | Range of change |
|---|---|---:|---:|---:|---:|
| `trees_5pp_from_paved` | +0.05 evergreen tree surface fraction, -0.05 paved fraction | 74.9 | 142.9 | +68.0 | +6 to +228 |
| `trees_10pp_from_paved` | +0.10 evergreen tree surface fraction, -0.10 paved fraction | 74.9 | 212.0 | +137.1 | +19 to +352 |
| `paved_albedo_035` | paved albedo set to 0.35 | 74.9 | 66.2 | -8.7 | -17 to -1 |
| `building_albedo_035` | building albedo set to 0.35 | 74.9 | 70.4 | -4.5 | -12 to 0 |

## Site Values

| Site | Baseline future hours | Trees +5pp | Trees +10pp | Paved albedo 0.35 | Building albedo 0.35 | Baseline future risk | Paved-albedo risk |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Jade Gardens | 20 | 39 | 78 | 15 | 19 | 0.00 | 0.00 |
| 2. Serendib Rise | 17 | 23 | 36 | 16 | 17 | 0.00 | 0.00 |
| 3. Taman Melati | 21 | 66 | 89 | 16 | 19 | 0.00 | 0.00 |
| 4. Kampong Lama | 103 | 122 | 265 | 88 | 99 | 0.76 | 0.74 |
| 5. Dhobi Lines | 96 | 108 | 274 | 84 | 91 | 0.73 | 0.71 |
| 6. Lusitano Square | 35 | 46 | 64 | 27 | 32 | 0.19 | 0.17 |
| 7. Mlima Moto | 126 | 316 | 446 | 115 | 118 | 0.83 | 0.83 |
| 8. Victoria Exchange | 55 | 143 | 196 | 46 | 50 | 0.21 | 0.20 |
| 9. Fuzhou Lanes | 211 | 439 | 563 | 194 | 199 | 1.00 | 1.00 |
| 10. Zheng He Towers | 65 | 127 | 109 | 61 | 60 | 0.00 | 0.00 |

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
