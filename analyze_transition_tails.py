"""
Transition-tail amplification analysis on the expanded Pantheon+ x DR9
sample.

Inputs:
  pantheon_dr9_multiscale.csv  (per-SN cone counts at 0.5, 1, 2 deg)

Builds:
  * per-scale standardized log-density rho_xx_std
  * local gradient d(log rho)/d(log r) via OLS across the three scales
  * across-scale log-density variance LV
  * sparse-reconnection score SR = max(log rho_2 - log rho_0.5, 0)
    (small-scale void embedded in larger-scale bulk)
  * neck_score = z(LV) + z(|GS|) + z(SR)

Tests (all on |resid_mu|):
  * Pearson + Spearman vs rho_10_std, GS, LV, SR, neck_score
  * Tail tests at the smallest and largest scales (P20 / P80 buckets)
  * Adversarial permutation (10k):
       (a) density scrambling: permute (n_05, n_10, n_20) tuples across SNe
       (b) angular scrambling: permute SN coords by reassigning density rows
           (operationally identical to (a) given fixed cone outputs --
            permuting the densities IS permuting which-SN-sees-what-sky)
       (c) corridor rewiring: permute SR only (preserve density+gradient
            marginals, break the void-in-bulk pairing)

Outputs:
  pantheon_dr9_topology.csv      (full per-SN feature table)
  topology_summary.csv           (correlation table)
  shuffle_results.csv            (empirical p-values)
  scatter_<feature>_vs_absresid.png  for rho, GS, LV, SR, neck_score
  Console summary + final checkpoint statement.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
IN_CSV = HERE / "pantheon_dr9_multiscale.csv"
OUT_FEATS = HERE / "pantheon_dr9_topology.csv"
OUT_CORR = HERE / "topology_summary.csv"
OUT_SHUF = HERE / "shuffle_results.csv"

N_SHUFFLES = 10_000
RNG_SEED = 20260524

# Effective cone areas (deg^2); for ratios the geometric factor cancels.
RADII = np.array([0.5, 1.0, 2.0])
LOG_R = np.log(RADII)
AREAS = np.pi * RADII ** 2


def standardize(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    mu = np.nanmean(a)
    sd = np.nanstd(a, ddof=1)
    return (a - mu) / sd if sd > 0 else a - mu


def safe_log_density(n: np.ndarray, area: float) -> np.ndarray:
    """log10((n+1)/area) -- the +1 keeps zero-density rows finite while
    preserving the ordering and the tail. The user explicitly asked not
    to treat zero density as junk."""
    return np.log10((n.astype(float) + 1.0) / area)


def per_sn_gradient(log_rho_matrix: np.ndarray) -> np.ndarray:
    """OLS slope of log_rho vs log_r for each SN row across the 3 scales."""
    x = LOG_R
    x_mean = x.mean()
    denom = np.sum((x - x_mean) ** 2)
    y = log_rho_matrix
    y_mean = y.mean(axis=1, keepdims=True)
    num = np.sum((x - x_mean) * (y - y_mean), axis=1)
    return num / denom


def pearson_spearman(x: np.ndarray, y: np.ndarray) -> dict:
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3:
        return dict(n=int(len(x)), pearson_r=np.nan, pearson_p=np.nan,
                    spearman_rho=np.nan, spearman_p=np.nan)
    pr = stats.pearsonr(x, y)
    sr = stats.spearmanr(x, y)
    return dict(n=int(len(x)), pearson_r=float(pr.statistic),
                pearson_p=float(pr.pvalue),
                spearman_rho=float(sr.statistic),
                spearman_p=float(sr.pvalue))


def empirical_p(stat_observed: float, stat_draws: np.ndarray) -> float:
    return float((np.abs(stat_draws) >= abs(stat_observed)).mean())


def scatter(x, y, xlab, ylab, title, path, labels=None, highlight=None):
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.axhline(0, color="0.75", lw=0.6)
    ax.scatter(x, y, s=24, alpha=0.85, edgecolor="black", linewidth=0.3)
    if highlight is not None:
        m = np.asarray(highlight, dtype=bool)
        ax.scatter(np.asarray(x)[m], np.asarray(y)[m], s=70,
                   facecolor="none", edgecolor="crimson", linewidth=1.4,
                   label=f"highlight (n={int(m.sum())})")
    if np.isfinite(x).sum() >= 3:
        slope, intercept, r, p, _ = stats.linregress(x[np.isfinite(x) & np.isfinite(y)],
                                                    y[np.isfinite(x) & np.isfinite(y)])
        xs = np.linspace(np.nanmin(x), np.nanmax(x), 50)
        ax.plot(xs, slope * xs + intercept, lw=1.0, color="steelblue",
                label=f"OLS  r={r:+.3f}  p={p:.3g}")
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(IN_CSV)
    # Drop rows with any failed query (-1), keep zero-counts.
    bad = (df[["n_05deg", "n_10deg", "n_20deg"]] < 0).any(axis=1)
    if bad.any():
        print(f"dropping {int(bad.sum())} rows with failed cone queries")
        df = df[~bad].reset_index(drop=True)

    n05 = df["n_05deg"].to_numpy()
    n10 = df["n_10deg"].to_numpy()
    n20 = df["n_20deg"].to_numpy()

    log_rho_05 = safe_log_density(n05, AREAS[0])
    log_rho_10 = safe_log_density(n10, AREAS[1])
    log_rho_20 = safe_log_density(n20, AREAS[2])

    log_rho_mat = np.column_stack([log_rho_05, log_rho_10, log_rho_20])

    rho_05_std = standardize(log_rho_05)
    rho_10_std = standardize(log_rho_10)
    rho_20_std = standardize(log_rho_20)

    # Local gradient and across-scale variance.
    GS = per_sn_gradient(log_rho_mat)        # d log rho / d log r
    LV = log_rho_mat.std(axis=1, ddof=1)     # multi-scale variance

    # Sparse reconnection: small-scale below large-scale (void embedded in bulk).
    SR = np.clip(log_rho_20 - log_rho_05, 0, None)

    GS_z = standardize(np.abs(GS))
    LV_z = standardize(LV)
    SR_z = standardize(SR)
    neck_score = GS_z + LV_z + SR_z

    df["log_rho_05"] = log_rho_05
    df["log_rho_10"] = log_rho_10
    df["log_rho_20"] = log_rho_20
    df["rho_05_std"] = rho_05_std
    df["rho_10_std"] = rho_10_std
    df["rho_20_std"] = rho_20_std
    df["grad_logrho_logr"] = GS
    df["abs_grad"] = np.abs(GS)
    df["multiscale_var"] = LV
    df["sparse_reconnection"] = SR
    df["neck_score"] = neck_score
    df["abs_resid"] = df["resid_mu"].abs()
    p20, p80 = np.percentile(n10, [20, 80])
    df["low_density_tail"] = (n10 < p20).astype(int)
    df["high_density_bulk"] = (n10 > p80).astype(int)

    df.to_csv(OUT_FEATS, index=False)

    abs_r = df["abs_resid"].to_numpy()
    resid = df["resid_mu"].to_numpy()
    features = {
        "rho_10_std":         df["rho_10_std"].to_numpy(),
        "rho_05_std":         df["rho_05_std"].to_numpy(),
        "rho_20_std":         df["rho_20_std"].to_numpy(),
        "abs_grad":           df["abs_grad"].to_numpy(),
        "multiscale_var":     df["multiscale_var"].to_numpy(),
        "sparse_reconnection":df["sparse_reconnection"].to_numpy(),
        "neck_score":         df["neck_score"].to_numpy(),
    }

    corr_rows = []
    for name, x in features.items():
        for target_name, target in [("resid_mu", resid), ("abs_resid", abs_r)]:
            s = pearson_spearman(x, target)
            s["feature"] = name
            s["target"] = target_name
            corr_rows.append(s)
    corr_df = pd.DataFrame(corr_rows)[
        ["feature", "target", "n", "pearson_r", "pearson_p",
         "spearman_rho", "spearman_p"]]
    corr_df.to_csv(OUT_CORR, index=False)

    # ---------- adversarial permutations ----------
    rng = np.random.default_rng(RNG_SEED)

    def obs_corr(x): return stats.pearsonr(abs_r, x).statistic

    obs = {k: obs_corr(v) for k, v in features.items() if k in
           {"rho_10_std", "neck_score", "sparse_reconnection", "abs_grad"}}

    n = len(df)
    # (a) density scrambling: permute the joint (n05,n10,n20) tuple across SNe.
    # This preserves the multi-scale covariance and the marginal distribution
    # while breaking the SN <-> sky pairing.
    n_mat = np.column_stack([n05, n10, n20])

    draws = {k: np.empty(N_SHUFFLES) for k in obs}
    for i in range(N_SHUFFLES):
        idx = rng.permutation(n)
        n_p = n_mat[idx]
        lr = np.column_stack([safe_log_density(n_p[:, 0], AREAS[0]),
                              safe_log_density(n_p[:, 1], AREAS[1]),
                              safe_log_density(n_p[:, 2], AREAS[2])])
        rho10 = standardize(lr[:, 1])
        gs = per_sn_gradient(lr)
        lv = lr.std(axis=1, ddof=1)
        sr = np.clip(lr[:, 2] - lr[:, 0], 0, None)
        gs_z = standardize(np.abs(gs))
        lv_z = standardize(lv)
        sr_z = standardize(sr)
        neck = gs_z + lv_z + sr_z
        draws["rho_10_std"][i] = stats.pearsonr(abs_r, rho10).statistic
        draws["neck_score"][i] = stats.pearsonr(abs_r, neck).statistic
        draws["sparse_reconnection"][i] = stats.pearsonr(abs_r, sr).statistic
        draws["abs_grad"][i] = stats.pearsonr(abs_r, np.abs(gs)).statistic

    shuffle_rows = []
    for k, observed in obs.items():
        p_emp = empirical_p(observed, draws[k])
        shuffle_rows.append({
            "feature": k,
            "observed_pearson_r_vs_abs_resid": observed,
            "n_shuffles": N_SHUFFLES,
            "empirical_p_two_sided": p_emp,
            "test": "density-tuple scrambling",
        })

    # (c) corridor rewiring -- permute SR alone (break void-in-bulk pairing
    # while keeping rho and gradient untouched).
    sr_arr = df["sparse_reconnection"].to_numpy()
    sr_obs = stats.pearsonr(abs_r, sr_arr).statistic
    sr_draws = np.empty(N_SHUFFLES)
    for i in range(N_SHUFFLES):
        sr_draws[i] = stats.pearsonr(abs_r, sr_arr[rng.permutation(n)]).statistic
    shuffle_rows.append({
        "feature": "sparse_reconnection",
        "observed_pearson_r_vs_abs_resid": sr_obs,
        "n_shuffles": N_SHUFFLES,
        "empirical_p_two_sided": empirical_p(sr_obs, sr_draws),
        "test": "corridor rewiring (SR-only permutation)",
    })

    shuf_df = pd.DataFrame(shuffle_rows)
    shuf_df.to_csv(OUT_SHUF, index=False)

    # ---------- tail bucket diagnostics ----------
    low = df["low_density_tail"].to_numpy().astype(bool)
    high = df["high_density_bulk"].to_numpy().astype(bool)
    mid = ~(low | high)
    bucket_rows = []
    for name, mask in [("low_density_tail (<P20 of n_10deg)", low),
                       ("middle (P20-P80)", mid),
                       ("high_density_bulk (>P80)", high)]:
        if mask.any():
            r = resid[mask]
            bucket_rows.append({
                "bucket": name,
                "n": int(mask.sum()),
                "mean_resid": float(np.mean(r)),
                "median_resid": float(np.median(r)),
                "mean_abs_resid": float(np.mean(np.abs(r))),
                "std_resid": float(np.std(r, ddof=1)) if mask.sum() > 1 else float("nan"),
            })
    bucket_df = pd.DataFrame(bucket_rows)
    bucket_df.to_csv(HERE / "tail_buckets.csv", index=False)

    # Mann-Whitney: |resid| in low-density tail vs rest.
    if low.any() and (~low).any():
        u = stats.mannwhitneyu(abs_r[low], abs_r[~low], alternative="greater")
        mw = {"test": "Mann-Whitney U (abs_resid: low-density tail > rest)",
              "U": float(u.statistic), "p_one_sided": float(u.pvalue),
              "n_tail": int(low.sum()), "n_rest": int((~low).sum())}
    else:
        mw = {"test": "skip", "note": "no tail"}

    # ---------- scatter plots ----------
    cid = df["CID"].tolist()
    scatter(df["rho_10_std"].to_numpy(), abs_r, "rho_std (log n_10deg)",
            "|resid_mu|",
            f"|residual| vs 1-deg density  (n={len(df)})",
            HERE / "scatter_absresid_vs_rho.png", labels=cid, highlight=low)
    scatter(df["abs_grad"].to_numpy(), abs_r, "|d log rho / d log r|",
            "|resid_mu|",
            f"|residual| vs multi-scale density gradient  (n={len(df)})",
            HERE / "scatter_absresid_vs_grad.png", labels=cid, highlight=low)
    scatter(df["multiscale_var"].to_numpy(), abs_r, "log-density std across 3 scales",
            "|resid_mu|",
            f"|residual| vs multi-scale variance  (n={len(df)})",
            HERE / "scatter_absresid_vs_LV.png", labels=cid, highlight=low)
    scatter(df["sparse_reconnection"].to_numpy(), abs_r,
            "max(log rho_2 - log rho_0.5, 0)", "|resid_mu|",
            f"|residual| vs sparse-reconnection score  (n={len(df)})",
            HERE / "scatter_absresid_vs_SR.png", labels=cid, highlight=low)
    scatter(df["neck_score"].to_numpy(), abs_r,
            "neck_score = z(|GS|)+z(LV)+z(SR)", "|resid_mu|",
            f"|residual| vs transition-neck score  (n={len(df)})",
            HERE / "scatter_absresid_vs_neckscore.png",
            labels=cid, highlight=low)

    # ---------- console summary ----------
    print("=" * 78)
    print(f"SAMPLE  n={len(df)}  (DEC>-20, zCMB>0.01, non-calibrators)")
    print("=" * 78)
    print(f"  zCMB     [{df.zCMB.min():.3f}, {df.zCMB.max():.3f}]")
    print(f"  DEC      [{df.DEC.min():.2f}, {df.DEC.max():.2f}]")
    print(f"  n_10deg  median={np.median(n10):.0f}  zeros={(n10==0).sum()}")
    print(f"  abs_resid  mean={abs_r.mean():.4f}  std={abs_r.std():.4f}")
    print()
    print("CORRELATIONS vs abs_resid")
    for r in corr_rows:
        if r["target"] != "abs_resid":
            continue
        print(f"  {r['feature']:22s}  "
              f"Pearson r={r['pearson_r']:+.3f} (p={r['pearson_p']:.3g})   "
              f"Spearman rho={r['spearman_rho']:+.3f} (p={r['spearman_p']:.3g})")
    print()
    print("ADVERSARIAL PERMUTATION (10000 draws, vs abs_resid)")
    for row in shuffle_rows:
        print(f"  {row['feature']:22s}  obs r={row['observed_pearson_r_vs_abs_resid']:+.3f}  "
              f"emp p={row['empirical_p_two_sided']:.4f}   [{row['test']}]")
    print()
    print("TAIL BUCKETS")
    print(bucket_df.to_string(index=False))
    print()
    print("  ", mw)

    # ---------- checkpoint conclusion ----------
    rho_r = next(r for r in corr_rows if r["feature"] == "rho_10_std" and r["target"] == "abs_resid")
    neck_r = next(r for r in corr_rows if r["feature"] == "neck_score" and r["target"] == "abs_resid")
    sr_r = next(r for r in corr_rows if r["feature"] == "sparse_reconnection" and r["target"] == "abs_resid")
    rho_shuf = next(s for s in shuffle_rows if s["feature"] == "rho_10_std")

    survives_density = rho_shuf["empirical_p_two_sided"] < 0.05
    tail_anomalous = mw.get("p_one_sided", 1.0) < 0.05 if "p_one_sided" in mw else False

    print()
    print("=" * 78)
    print("CHECKPOINT")
    print("=" * 78)
    print(f"  |resid| vs density (rho_10_std):       r={rho_r['pearson_r']:+.3f}  "
          f"emp p={rho_shuf['empirical_p_two_sided']:.4f}  "
          f"-> {'SURVIVES' if survives_density else 'fails'} shuffling")
    print(f"  |resid| vs neck_score:                 r={neck_r['pearson_r']:+.3f}  "
          f"(p={neck_r['pearson_p']:.3g})")
    print(f"  |resid| vs sparse_reconnection:        r={sr_r['pearson_r']:+.3f}  "
          f"(p={sr_r['pearson_p']:.3g})")
    print(f"  Low-density tail amplification (MW p): {mw.get('p_one_sided', float('nan')):.4f}  "
          f"-> {'TAIL ANOMALOUS' if tail_anomalous else 'tail not anomalous'}")


if __name__ == "__main__":
    main()
