#!/usr/bin/env python3
"""Evaluate model predictions vs Pinnacle close: logloss/Brier, calibration,
value-backtest at closing prices. Saves results JSON + figures.
No em dashes in outputs."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "/home/hatch/workspace/o1-authorship/betting-paper"

def load():
    return json.load(open(f"{BASE}/data/model_predictions.json"))

def pinn_implied(pch, pcd, pca):
    inv = np.array([1/pch, 1/pcd, 1/pca])
    return inv / inv.sum()

def outcome_idx(hg, ag):
    return 0 if hg > ag else (1 if hg == ag else 2)

def metrics(preds, key):
    n = len(preds); ll = br = pll = pbr = 0.0; nx = 0
    for m in preds:
        p = np.array(m[key]); q = pinn_implied(m["pch"], m["pcd"], m["pca"])
        y = np.zeros(3); y[outcome_idx(m["hg"], m["ag"])] = 1
        p = np.clip(p, 1e-6, 1 - 1e-6); q = np.clip(q, 1e-6, 1 - 1e-6)
        ll -= np.sum(y * np.log(p)); br += np.sum((p - y) ** 2)
        pll -= np.sum(y * np.log(q)); pbr += np.sum((q - y) ** 2)
        nx += 1
    return {"n": nx, "logloss": ll/nx, "brier": br/nx,
            "pinn_logloss": pll/nx, "pinn_brier": pbr/nx}

def calibration(preds, key, nbins=10):
    """Pooled binary calibration over all (match, outcome) pairs."""
    ps, ys = [], []
    for m in preds:
        y = outcome_idx(m["hg"], m["ag"])
        for k in range(3):
            ps.append(m[key][k]); ys.append(1 if k == y else 0)
    ps = np.array(ps); ys = np.array(ys)
    edges = np.linspace(0, 1, nbins + 1)
    out = []
    for b in range(nbins):
        lo, hi = edges[b], edges[b+1]
        sel = (ps > lo) & (ps <= hi) if b > 0 else (ps >= lo) & (ps <= hi)
        if sel.sum() < 20: continue
        out.append({"bin_center": float((lo+hi)/2), "mean_pred": float(ps[sel].mean()),
                    "obs_freq": float(ys[sel].mean()), "n": int(sel.sum())})
    ece = sum(abs(r["obs_freq"] - r["mean_pred"]) * r["n"] for r in out) / sum(r["n"] for r in out)
    return out, ece

def backtest(preds, key, edge=0.03):
    """Flat 1u bets when model_prob >= (1+edge)*pinn_implied, settled at Pinnacle close."""
    odds = {"pch": 0, "pcd": 1, "pca": 2}
    keys = ["pch", "pcd", "pca"]
    profit = 0.0; bets = 0; wins = 0; returns = []
    for m in preds:
        p = np.array(m[key]); q = pinn_implied(m["pch"], m["pcd"], m["pca"])
        o = np.array([m["pch"], m["pcd"], m["pca"]])
        y = outcome_idx(m["hg"], m["ag"])
        for k in range(3):
            if p[k] >= (1 + edge) * q[k]:
                bets += 1
                r = (o[k] - 1) if k == y else -1.0
                profit += r; returns.append(r)
                if k == y: wins += 1
    returns = np.array(returns)
    roi = profit / bets if bets else 0
    t = (returns.mean() / (returns.std(ddof=1) / np.sqrt(bets))) if bets > 1 and returns.std() > 0 else 0
    return {"edge": edge, "bets": bets, "wins": wins,
            "strike": wins/bets if bets else 0, "profit_u": round(profit, 2),
            "roi": round(roi, 4), "t_stat": round(float(t), 2)}

def main():
    preds = load()
    print(f"predictions: {len(preds)}")
    res = {}
    for key, label in [("dc", "Dixon-Coles (goals)"), ("xg", "xG Poisson")]:
        sub = [m for m in preds if m[key] is not None]
        res[label] = {"metrics": metrics(sub, key)}
        cal, ece = calibration(sub, key)
        res[label]["ece"] = round(ece, 4)
        res[label]["calibration"] = cal
        res[label]["backtests"] = {f"edge_{int(e*100)}pct": backtest(sub, key, e)
                                   for e in [0.0, 0.02, 0.05]}
        print(f"\n{label}: n={len(sub)}")
        print("  ", res[label]["metrics"])
        print("   ECE:", res[label]["ece"])
        for b in res[label]["backtests"].values(): print("  ", b)
    json.dump(res, open(f"{BASE}/results/evaluation.json", "w"), indent=1)

    # Figure 1: calibration curves
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for key, label, ls in [("dc", "Dixon-Coles (goals)", "-"), ("xg", "xG Poisson", "--")]:
        sub = [m for m in preds if m[key] is not None]
        cal, _ = calibration(sub, key)
        xs = [r["mean_pred"] for r in cal]; ys = [r["obs_freq"] for r in cal]
        ax.plot(xs, ys, marker="o", linestyle=ls, label=label)
    ax.plot([0, 1], [0, 1], "k:", label="Perfect calibration")
    ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Observed frequency")
    ax.set_title("Calibration: model probability vs observed outcome rate\n(8,982 matches, 5 leagues, 2020/21 to 2024/25)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(f"{BASE}/results/figure1_calibration.png", dpi=150)

    # Figure 2: backtest equity (edge 3%)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=False)
    for ax, (key, label) in zip(axes, [("dc", "Dixon-Coles (goals)"), ("xg", "xG Poisson")]):
        sub = [m for m in preds if m[key] is not None]
        eq, n = [0], 0
        for m in sorted(sub, key=lambda m: m["date"]):
            p = np.array(m[key]); q = pinn_implied(m["pch"], m["pcd"], m["pca"])
            o = np.array([m["pch"], m["pcd"], m["pca"]])
            y = outcome_idx(m["hg"], m["ag"])
            for k in range(3):
                if p[k] >= 1.03 * q[k]:
                    eq.append(eq[-1] + ((o[k]-1) if k == y else -1.0)); n += 1
        ax.plot(eq, linewidth=1.2)
        ax.set_title(f"{label}: cumulative P/L at 3% edge ({n} bets)")
        ax.set_xlabel("Bet number"); ax.set_ylabel("Profit (units)")
        ax.grid(alpha=0.3); ax.axhline(0, color="k", linewidth=0.8)
    fig.tight_layout(); fig.savefig(f"{BASE}/results/figure2_backtest.png", dpi=150)
    print("\nsaved results/evaluation.json, figure1_calibration.png, figure2_backtest.png")

if __name__ == "__main__":
    main()
