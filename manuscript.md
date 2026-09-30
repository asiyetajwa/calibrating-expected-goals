# Calibrating Expected Goals: An Out-of-Sample Test of xG-Based Match Probabilities Against Pinnacle Closing Lines

**Brian Simiyu**
**Founder, Dribble (dribble360.com)**
**bw@dribble360.com**

October 2026. Working paper.

## Abstract

We test whether team ratings built from expected goals (xG) produce better
probabilistic forecasts of football match outcomes than a classical goals-based
model, using Pinnacle closing odds as the efficiency benchmark. Our sample
covers 8,982 matches from Europe's top five leagues across the 2020/21 to
2024/25 seasons. We join historical Pinnacle closing 1X2 prices with
team-level expected goals from the dribble360 football data API and generate
strictly out-of-sample forecasts from two walk-forward models: a time-decayed
Dixon-Coles goal model and a Poisson model driven by time-weighted xG ratings.
Both models are well calibrated, with expected calibration errors of 0.014 and
0.035. The goals-based Dixon-Coles model is marginally sharper than the xG
variant on log loss (1.001 vs 1.017) and Brier score (0.597 vs 0.609), while
Pinnacle's closing implied probabilities remain the sharpest of all (log loss
0.969, Brier 0.576). A flat-stake backtest wagering on model-identified value
at closing prices loses 4 to 7 percent ROI with significant negative t-stats,
consistent with strong-form efficiency of the football closing line. We
conclude that xG ratings yield well-calibrated probabilities but, in the
simple time-weighted specification tested here, do not improve on a well-fit
goals model and do not beat the market.

Keywords: expected goals, football forecasting, Dixon-Coles, Poisson model,
calibration, betting market efficiency, Pinnacle.

## 1. Introduction

Probabilistic forecasting of association football outcomes has a long
quantitative tradition. Maher (1982) introduced the independent Poisson goal
model, and Dixon and Coles (1997) extended it with a time-decay weighting and
a correction for dependence in low-scoring matches, a specification that
remains the workhorse of the field. Rue and Salvesen (2000) developed a
Bayesian dynamic alternative. In parallel, expected goals (xG), which values
each shot by its estimated scoring probability, has become the standard
measure of chance quality in professional analytics, on the argument that shot
volumes and locations carry more signal about team strength than goals alone.

Whether xG-based team ratings actually forecast better than goals-based
ratings is less settled than practitioners sometimes assume. Goals are noisy,
but xG models introduce their own estimation error, and the mapping from
chance creation to goals scored is itself stochastic. The natural benchmark
for any forecasting model is the betting market, and specifically the
Pinnacle closing line, which the sports forecasting literature widely treats
as the most efficient publicly observable probability estimate.

This paper makes three contributions. First, we assemble a large out-of-sample
test set: 8,982 matches from the English Premier League, Spanish La Liga,
Italian Serie A, German Bundesliga, and French Ligue 1 over five seasons
(2020/21 to 2024/25), each with Pinnacle closing 1X2 odds and team-level xG
joined from an independent data provider. Second, we compare two walk-forward
forecasting models head to head: a time-decayed Dixon-Coles model fit on
goals, and a Poisson model driven by time-weighted xG attack and defense
ratings. Every forecast uses only information available before the match
date. Third, we evaluate both models on proper scoring rules, calibration,
and a wagering backtest against the closing line.

Our headline findings are sober. Both models are well calibrated. The
goals-based Dixon-Coles model is slightly sharper than the xG variant, and
neither approaches the sharpness of Pinnacle's closing prices. Wagering on
model-identified value at closing odds loses money at a statistically
significant rate. xG ratings produce honest probabilities, but they do not, in
the specification tested here, beat a well-fit goals model or the market.

## 2. Data

Match results and historical odds come from football-data.co.uk, which
publishes free historical CSV files covering more than 25 leagues and 20
seasons. We use the 2020/21 through 2024/25 seasons for the five leagues
above: 8,982 matches in total, each with full-time scoreline and Pinnacle
opening and closing 1X2 odds, alongside prices from other bookmakers.

Team expected goals come from the dribble360 football data API, which serves
Opta-sourced match aggregates. For each team and match we pull expected goals
scored and expected goals conceded. Because the two sources use different
team naming conventions, we join on match date plus team name through a
hand-verified 132-name alias map. As a validation check, we compare the
dribble360 scoreline against the odds-source scoreline wherever both record
goals: agreement is 99.98 percent across 4,594 matched games, confirming the
join. Both teams' xG is available for 8,454 of the 8,982 matches (94.1
percent); the remainder lack team-level stat rows in the API archive.

## 3. Methods

### 3.1 Walk-forward protocol

For each league, matches are ordered by date. A match is forecast only if
both teams have at least six prior league matches in the training history,
which removes the unreliable early-season period. The first forecast dates
fall in autumn 2020. All model parameters for a forecast are estimated from
matches played strictly before the forecast date. This yields 8,483
out-of-sample forecasts for the goals model and 8,005 for the xG model (the
difference reflects xG availability).

### 3.2 Model 1: time-decayed Dixon-Coles

Following Dixon and Coles (1997), home goals and away goals are modelled as
conditionally independent Poisson variables with means

lambda = exp(home + attack_h + defense_a),
mu = exp(attack_a + defense_h),

with a multiplicative adjustment governed by a dependence parameter rho for
the four lowest scorelines. Match contributions to the likelihood are
weighted by exp(-xi * days), with xi = 0.002, so recent matches count more.
Parameters are estimated by maximum likelihood under the constraint that mean
attack strength is zero, refit monthly within each league. Outcome
probabilities come from the Poisson scoreline matrix truncated at ten goals
per team.

### 3.3 Model 2: xG Poisson

Each team's attack rating is its time-weighted average xG scored and its
defense rating its time-weighted average xG conceded, using the same decay
xi = 0.002 over prior matches. The home advantage is estimated as the mean
home-minus-away xG difference over the trailing 400 league matches. Expected
goals for the fixture are (attack_h + defense_a)/2 plus or minus half the
home edge, and outcome probabilities again come from the Poisson scoreline
matrix. This is deliberately a simple specification: it asks whether plain
xG averages, without further modelling, improve on goals.

### 3.4 Evaluation

We report log loss and Brier score for each model against the same metrics
computed from Pinnacle closing implied probabilities (overround removed by
normalization). Calibration is assessed with a pooled reliability diagram
over all match-outcome pairs and summarized by the expected calibration
error (ECE) across decile bins. Finally, we run a flat-stake backtest: bet
one unit on any outcome where the model probability exceeds the Pinnacle
implied probability by a threshold edge (0, 2, and 5 percent), settling at
Pinnacle closing odds, and report ROI with t-stats.

## 4. Results

### 4.1 Sharpness

Table 1 reports proper scores. Pinnacle's closing line is the sharpest
forecaster by a clear margin, as expected. Between the two models, the
goals-based Dixon-Coles model is marginally sharper than the xG Poisson on
both log loss and Brier score. The gap is small but consistent: modeling
goals directly with a properly fit likelihood beats modelling smoothed xG
averages in this sample.

Table 1: Out-of-sample accuracy vs the Pinnacle closing line.

| Model               | n     | Log loss | Brier | ECE   | Pin log loss | Pin Brier |
|---------------------|-------|----------|-------|-------|-------------------|----------------|
| Dixon-Coles (goals) | 8,483 | 1.001    | 0.597 | 0.014 | 0.969             | 0.576          |
| xG Poisson          | 8,005 | 1.017    | 0.609 | 0.035 | 0.975             | 0.580          |

### 4.2 Calibration

Figure 1 shows the reliability diagram. Both models track the diagonal
closely through the middle of the probability range. The Dixon-Coles model
is nearly perfectly calibrated (ECE 0.014). The xG model is slightly
overconfident at high probabilities and underconfident at low ones (ECE
0.035), but remains far better calibrated than an uncalibrated heuristic
would be. In practical terms, both models' stated probabilities mean what
they say.

### 4.3 Backtest against the closing line

Table 2 and Figure 2 show the wagering results. At every edge threshold,
betting model-identified value at Pinnacle closing prices loses money. The
Dixon-Coles model loses 4.3 to 5.5 percent ROI over roughly ten to twelve
thousand bets; the xG model loses 6.6 to 6.9 percent. All t-stats are
negative and significant. The equity curves decline steadily rather than in
jumps, indicating a systematic shortfall against the closing line rather
than a few bad beats. This is the standard signature of a market that has
already incorporated the information in these models.

Table 2: Flat-stake backtest, 1 unit per bet, settled at Pinnacle closing
odds. A bet is placed when model probability >= (1 + edge) * Pinnacle
implied probability.

| Model       | Edge | Bets   | Strike | Profit (units) | ROI    | t-stat |
|-------------|------|--------|--------|----------------|--------|--------|
| Dixon-Coles | 0%   | 12,391 | 30.7%  | -564.3         | -4.6%  | -2.89  |
| Dixon-Coles | 2%   | 11,284 | 30.2%  | -487.6         | -4.3%  | -2.57  |
| Dixon-Coles | 5%   | 9,712  | 28.8%  | -538.0         | -5.5%  | -3.03  |
| xG Poisson  | 0%   | 12,001 | 22.9%  | -795.5         | -6.6%  | -3.73  |
| xG Poisson  | 2%   | 11,294 | 22.4%  | -746.6         | -6.6%  | -3.56  |
| xG Poisson  | 5%   | 10,327 | 21.5%  | -711.8         | -6.9%  | -3.48  |

## 5. Discussion

Three points deserve emphasis. First, calibration and sharpness are
different virtues, and both models have the first while lacking the second
relative to the market. A well-calibrated model is still useful for risk
management, simulation, and pricing derivatives of match outcomes even when
it cannot beat the closing line.

Second, the xG model's failure to beat the goals model should be read
narrowly. We tested simple time-weighted xG averages, not an xG-native
likelihood or a model that uses shot-level detail. Richer xG specifications,
including separate ratings for open play and set pieces or score-state
adjustments, might do better. Our result is that xG does not help by
default; it must earn its place through modelling.

Third, the backtest uses closing odds, the hardest benchmark in sports
wagering. Losing to the close does not imply the models contain no
information; it implies the market already contains it. An interesting
extension would test the models against opening odds to measure closing
line value, which requires timestamped odds movement data we do not have.

Limitations include the restriction to Europe's top five leagues, the use
of a single xG provider's aggregates, and the simple form of the xG model
noted above.

## 6. Conclusion

On 8,483 out-of-sample forecasts across five seasons, expected-goals team
ratings produce well-calibrated match probabilities but do not improve on a
classical time-decayed Dixon-Coles goal model, and neither model beats
Pinnacle's closing line. The closing line remains the best available
probability estimate, and the wagering results are consistent with
strong-form market efficiency. For practitioners, the message is that xG is
a sound input to calibrated forecasting systems, not a shortcut around the
market.

## References

Dixon, M. J., and Coles, S. G. (1997). Modelling association football scores
and inefficiencies in the football betting market. Applied Statistics, 46(2),
265-280.

Maher, M. J. (1982). Modelling association football scores. Statistica
Neerlandica, 36(3), 109-118.

Rue, H., and Salvesen, O. (2000). Prediction and retrospective analysis of
soccer matches in a league. Journal of the Royal Statistical Society: Series
D (The Statistician), 49(3), 399-418.

## Data and code availability

Match results and historical odds: football-data.co.uk (free download).
Team expected goals: dribble360 API (https://dribble360.com). Analysis code
and derived results are available in the public repository accompanying this
paper. Raw Opta-sourced event aggregates are not redistributed; only code
and derived outputs are published, per the data license.
