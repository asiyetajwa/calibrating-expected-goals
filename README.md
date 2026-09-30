# Calibrating Expected Goals

**Brian Simiyu**, Founder, Dribble (dribble360.com) — October 2026. Working paper.

An out-of-sample test of xG-based match probabilities against Pinnacle closing lines.

## What this is

We test whether team ratings built from expected goals (xG) produce better probabilistic forecasts of football match outcomes than a classical goals-based model, using Pinnacle closing odds as the efficiency benchmark.

- **Sample:** 8,982 matches, Europe's top five leagues, 2020/21 to 2024/25.
- **Odds:** Pinnacle closing 1X2 prices from football-data.co.uk (free historical CSVs).
- **xG:** team-level expected goals from the dribble360 football data API (Opta-sourced), joined on date plus team name via a hand-verified 132-name alias map (99.98% scoreline agreement on the validation subset).
- **Models:** two walk-forward forecasters using only prior matches:
  1. Time-decayed Dixon-Coles goal model (8,483 forecasts).
  2. Time-weighted xG Poisson model (8,005 forecasts).

## Headline results

| Model | Log loss | Brier | ECE | Pinnacle log loss | Pinnacle Brier |
|---|---|---|---|---|---|
| Dixon-Coles (goals) | 1.001 | 0.597 | 0.014 | 0.969 | 0.576 |
| xG Poisson | 1.017 | 0.609 | 0.035 | 0.975 | 0.580 |

Flat-stake backtest on model-identified value at Pinnacle closing prices (2% edge): Dixon-Coles ROI -4.3% (t=-2.57), xG Poisson ROI -6.6% (t=-3.56).

Both models are well calibrated, the goals-based Dixon-Coles model is marginally sharper than the xG variant, and neither beats Pinnacle's closing line.

## Contents

- `manuscript.md` — full working paper.
- `results/Calibrating_Expected_Goals_Simiyu_2026.pdf` — paper PDF.
- `results/RESULTS.md` — detailed results with tables.
- `results/evaluation.json` — all computed metrics.
- `results/figure1_calibration.png`, `results/figure2_backtest.png` — figures.
- `scripts/` — pipeline: data pull, join/validation, dataset build, model fitting, evaluation, PDF rendering.

## Reproducing

Raw match data is not redistributed (see below). To reproduce:

1. Download the football-data.co.uk season CSVs into `data/odds/`.
2. Pull team matches from the dribble360 API into `data/dribble360/` (requires a dribble360 API key).
3. Run the scripts in order: `pull_team_matches.py`, `join_validate.py`, `build_dataset.py`, `model_fit.py`, `evaluate.py`.

`results/evaluation.json` contains every number reported in the paper, so all tables and claims can be checked without re-running the models.

## Data and license

Match results and historical odds: football-data.co.uk (free download). Team expected goals: dribble360 API (https://dribble360.com). Raw Opta-sourced event aggregates are not redistributed; this repository publishes code and derived outputs only, per the data license.
