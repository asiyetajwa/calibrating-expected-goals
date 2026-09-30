#!/usr/bin/env python3
"""Walk-forward Dixon-Coles (goals) and xG-Poisson models vs Pinnacle close.
Vectorized xG computation. Outputs data/model_predictions.json.
No em dashes in outputs."""
import json, math
from datetime import datetime
import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson

BASE = "/home/hatch/workspace/o1-authorship/betting-paper"
XI = 0.002
MIN_PRIOR = 6
REFIT_DAYS = 30

def fit_dc(matches):
    teams = sorted({m[0] for m in matches} | {m[1] for m in matches})
    ti = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    H = np.array([ti[m[0]] for m in matches]); A = np.array([ti[m[1]] for m in matches])
    HG = np.array([m[2] for m in matches], float); AG = np.array([m[3] for m in matches], float)
    W = np.array([m[4] for m in matches], float)
    HGi = HG.astype(int); AGi = AG.astype(int)

    def nll(p):
        att = p[:n]; dfn = p[n:2*n]; home = p[2*n]; rho = p[2*n+1]
        lam = np.clip(np.exp(home + att[H] + dfn[A]), 1e-6, 12)
        mu = np.clip(np.exp(att[A] + dfn[H]), 1e-6, 12)
        ll = W * (poisson.logpmf(HGi, lam) + poisson.logpmf(AGi, mu))
        adj = np.ones(len(H))
        m00 = (HGi == 0) & (AGi == 0); m01 = (HGi == 0) & (AGi == 1)
        m10 = (HGi == 1) & (AGi == 0); m11 = (HGi == 1) & (AGi == 1)
        adj[m00] = 1 - lam[m00]*mu[m00]*rho
        adj[m01] = 1 + lam[m01]*rho
        adj[m10] = 1 + mu[m10]*rho
        adj[m11] = 1 - rho
        ll = ll + W * np.log(np.clip(adj, 1e-9, None))
        ll = ll - 1e4 * (np.mean(att) ** 2)
        return -np.sum(ll)

    p0 = np.zeros(2*n + 2); p0[2*n] = 0.25
    bounds = [(-2, 2)]*(2*n) + [(0, 1.5), (-0.3, 0.3)]
    res = minimize(nll, p0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": 200, "ftol": 1e-9})
    p = res.x
    return ({t: p[i] for i, t in enumerate(teams)},
            {t: p[n+i] for i, t in enumerate(teams)}, p[2*n], p[2*n+1])

def probs_1x2(lam, mu, rho=0.0):
    g = np.arange(0, 11)
    ph = poisson.pmf(g, min(max(lam, 0.02), 12)); pa = poisson.pmf(g, min(max(mu, 0.02), 12))
    M = np.outer(ph, pa)
    M[0,0] *= (1 - lam*mu*rho); M[0,1] *= (1 + lam*rho)
    M[1,0] *= (1 + mu*rho); M[1,1] *= (1 - rho)
    M = np.clip(M, 0, None); M /= M.sum()
    ph_ = np.tril(M, -1).sum()   # home goals > away goals
    pd_ = np.trace(M)            # draws
    pa_ = np.triu(M, 1).sum()    # away goals > home goals
    return ph_, pd_, pa_

def main():
    data = json.load(open(f"{BASE}/data/joined_matches.json"))
    by_league = {}
    for m in data:
        by_league.setdefault(m["league"], []).append(m)
    out = []
    for lg, ms in sorted(by_league.items()):
        ms.sort(key=lambda m: m["date"])
        N = len(ms)
        dord = np.array([datetime.strptime(m["date"], "%Y-%m-%d").date().toordinal() for m in ms])
        HT = np.array([m["home"] for m in ms]); AT = np.array([m["away"] for m in ms])
        HG = np.array([m["hg"] for m in ms], float); AG = np.array([m["ag"] for m in ms], float)
        HXG = np.array([m["hxg"] if m["hxg"] is not None else np.nan for m in ms])
        AXG = np.array([m["axg"] if m["axg"] is not None else np.nan for m in ms])
        HXGC = np.array([m["hxgc"] if m["hxgc"] is not None else np.nan for m in ms])
        AXGC = np.array([m["axgc"] if m["axgc"] is not None else np.nan for m in ms])
        print(f"{lg}: {N} matches", flush=True)

        # per-team match index lists for fast prior lookup
        from collections import defaultdict
        team_idx = defaultdict(list)
        for i in range(N):
            team_idx[HT[i]].append(i); team_idx[AT[i]].append(i)

        def wavg_vals(idxs, vals, d, upto):
            sel = [j for j in idxs if j < upto]
            if not sel: return None, 0
            v = vals[sel]; ok = ~np.isnan(v)
            if not ok.any(): return None, int(ok.sum())
            w = np.exp(-XI * (d - dord[sel][ok]))
            return float(np.sum(w * v[ok]) / np.sum(w)), int(ok.sum())

        def team_xg_for(team, d, upto):
            idxs = team_idx[team]
            sel = [j for j in idxs if j < upto]
            num = den = 0.0; cnt = 0
            for j in sel:
                w = math.exp(-XI * (d - dord[j]))
                if HT[j] == team and not np.isnan(HXG[j]):
                    num += w * HXG[j]; den += w; cnt += 1
                elif AT[j] == team and not np.isnan(AXG[j]):
                    num += w * AXG[j]; den += w; cnt += 1
            return (num / den if den > 0 else None), cnt

        def team_xg_against(team, d, upto):
            idxs = team_idx[team]
            sel = [j for j in idxs if j < upto]
            num = den = 0.0; cnt = 0
            for j in sel:
                w = math.exp(-XI * (d - dord[j]))
                if HT[j] == team and not np.isnan(HXGC[j]):
                    num += w * HXGC[j]; den += w; cnt += 1
                elif AT[j] == team and not np.isnan(AXGC[j]):
                    num += w * AXGC[j]; den += w; cnt += 1
            return (num / den if den > 0 else None), cnt

        cache = None; cache_d = None; nfits = 0; npred = 0
        for i in range(N):
            d = dord[i]; h = HT[i]; a = AT[i]
            ch = sum(1 for j in team_idx[h] if j < i)
            ca = sum(1 for j in team_idx[a] if j < i)
            if ch < MIN_PRIOR or ca < MIN_PRIOR:
                continue
            if cache is None or d - cache_d >= REFIT_DAYS:
                train = [(HT[j], AT[j], HG[j], AG[j], math.exp(-XI * (d - dord[j])))
                         for j in range(i)]
                att, dfn, home, rho = fit_dc(train)
                cache = (att, dfn, home, rho); cache_d = d; nfits += 1
            att, dfn, home, rho = cache
            lam = math.exp(home + att.get(h, 0) + dfn.get(a, 0))
            mu = math.exp(att.get(a, 0) + dfn.get(h, 0))
            dc = probs_1x2(lam, mu, rho)
            ha, _ = team_xg_for(h, d, i); hd, _ = team_xg_against(h, d, i)
            aa, _ = team_xg_for(a, d, i); ad, _ = team_xg_against(a, d, i)
            xgp = None
            if None not in (ha, hd, aa, ad):
                # home edge from recent xG goal difference
                j0 = max(0, i - 400)
                diff = []
                for j in range(j0, i):
                    if not np.isnan(HXG[j]) and not np.isnan(AXG[j]):
                        diff.append(HXG[j] - AXG[j])
                hfa = float(np.mean(diff)) if diff else 0.25
                lamx = max(0.05, (ha + ad) / 2 + hfa / 2)
                mux = max(0.05, (aa + hd) / 2 - hfa / 2)
                xgp = probs_1x2(lamx, mux)
            m = ms[i]
            out.append({"date": m["date"], "league": lg, "home": h, "away": a,
                        "hg": m["hg"], "ag": m["ag"],
                        "pch": m["pch"], "pcd": m["pcd"], "pca": m["pca"],
                        "dc": [round(float(x), 4) for x in dc],
                        "xg": [round(float(x), 4) for x in xgp] if xgp else None})
            npred += 1
        print(f"  predictions: {npred}, refits: {nfits}", flush=True)
    json.dump(out, open(f"{BASE}/data/model_predictions.json", "w"))
    print(f"TOTAL: {len(out)}")

if __name__ == "__main__":
    main()
