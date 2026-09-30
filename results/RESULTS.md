# Paper 2: Results (computed 2026-10-01)

## Data
- 8,982 matches, 5 leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1),
  seasons 2020/21 through 2024/25.
- Odds: football-data.co.uk historical CSVs, free, no key. Pinnacle closing
  1X2 odds (PSCH/PSCD/PSCA) as the efficiency benchmark.
- Team xG: dribble360 API team_matches (expected_goals, expected_goals_conceded),
  joined on date + team name via a 132-name alias map. Scoreline agreement on the
  join: 99.98%. Both sides xG present for 8,454 of 8,982 matches (94.1%).

## Models (walk-forward, strictly out-of-sample)
- M1 Dixon-Coles (goals): time-decayed weighted MLE (xi=0.002), attack/defense
  per team, home advantage, rho correction. Refit monthly per league. Min 6 prior
  matches per team before first prediction.
- M2 xG Poisson: time-weighted average xG scored/conceded per team, home edge
  from recent xG goal difference, independent Poisson scoreline matrix.
- Predictions: 8,483 (M1), 8,005 (M2).

## Table 1: Out-of-sample accuracy vs Pinnacle closing line
| Model | n | Log loss | Brier | ECE | Pinnacle log loss | Pinnacle Brier |
|---|---|---|---|---|---|---|
| Dixon-Coles (goals) | 8,483 | 1.001 | 0.597 | 0.014 | 0.969 | 0.576 |
| xG Poisson | 8,005 | 1.017 | 0.609 | 0.035 | 0.975 | 0.580 |

## Table 2: Flat-stake backtest, 1 unit per bet, settled at Pinnacle closing odds
Bet when model_prob >= (1+edge) * pinnacle_implied_prob.
| Model | Edge | Bets | Strike | Profit (u) | ROI | t-stat |
|---|---|---|---|---|---|---|
| Dixon-Coles | 0% | 12,391 | 30.7% | -564.3 | -4.6% | -2.89 |
| Dixon-Coles | 2% | 11,284 | 30.2% | -487.6 | -4.3% | -2.57 |
| Dixon-Coles | 5% | 9,712 | 28.8% | -538.0 | -5.5% | -3.03 |
| xG Poisson | 0% | 12,001 | 22.9% | -795.5 | -6.6% | -3.73 |
| xG Poisson | 2% | 11,294 | 22.4% | -746.6 | -6.6% | -3.56 |
| xG Poisson | 5% | 10,327 | 21.5% | -711.8 | -6.9% | -3.48 |

## Reading
- Both models are well calibrated (Figure 1). The goals-based Dixon-Coles is
  marginally sharper than the simple xG-averages variant on both proper scores.
- Neither model beats Pinnacle's closing line. Wagering model-identified value
  at closing prices loses 4 to 7 percent ROI with significant negative t-stats.
  This is consistent with strong-form efficiency of the football closing line
  reported in the literature.
- Honest paper frame: a large-scale out-of-sample calibration and market
  efficiency test, not a winning system. The xG-vs-goals comparison (simple xG
  averages do not beat a well-fit goals model) is itself a publishable finding.

## Figures
- figure1_calibration.png: reliability diagram, both models vs perfect line.
- figure2_backtest.png: cumulative P/L equity curves at 3% edge.
