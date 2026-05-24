"""
Merge Pantheon feature table with DR9 1-degree density counts and probe whether
the coupled topology proxy kappa x rho (and the low-density tail) outperforms
density alone as a predictor of mu-residuals.

Constraints honored:
  * No global averaging before correlations.
  * Zero / low-density rows are kept (2007ca falls south of DR9 footprint).
  * Tail structure preserved via 20th / 80th percentile masks.
  * Shuffle test built on rho permutations, recomputing kappa x rho each draw.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
COUNTS_CSV = HERE / "pantheon_next_counts.csv"
FEATURES_CSV = HERE / "pantheon_features.csv"
MERGED_CSV = HERE / "pantheon_dr9_merged.csv"
SUMMARY_CSV = HERE / "pantheon_dr9_summary.csv"
PLOT_RHO = HERE / "scatter_resid_vs_rho.png"
PLOT_KXR_RESID = HERE / "scatter_resid_vs_kappa_x_rho.png"
PLOT_KXR_ABS = HERE / "scatter_absresid_vs_kappa_x_rho.png"

N_SHUFFLES = 10_000
RNG_SEED = 20260524


def dedupe_pantheon(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate by CID. If a resid uncertainty column exists, keep the row
    with the smallest |uncertainty|; otherwise keep the first non-null resid."""
    if df["CID"].is_unique:
        return df.copy()

    unc_cols = [c for c in df.columns if c.lower() in {"resid_mu_err", "mu_err", "sigma_mu"}]
    out = []
    for cid, grp in df.groupby("CID", sort=False):
        if unc_cols:
            unc = grp[unc_cols[0]].abs()
            if unc.notna().any():
                out.append(grp.loc[unc.idxmin()])
                continue
        valid = grp[grp["resid_mu"].notna()]
        out.append((valid if len(valid) else grp).iloc[0])
    return pd.DataFrame(out).reset_index(drop=True)


def standardize(x: np.ndarray) -> np.ndarray:
    mu = np.mean(x)
    sd = np.std(x, ddof=1)
    return (x - mu) / sd if sd > 0 else x - mu


def pearson_spearman(x: np.ndarray, y: np.ndarray) -> dict:
    pr = stats.pearsonr(x, y)
    sr = stats.spearmanr(x, y)
    return {
        "pearson_r": float(pr.statistic),
        "pearson_p": float(pr.pvalue),
        "spearman_rho": float(sr.statistic),
        "spearman_p": float(sr.pvalue),
        "n": int(len(x)),
    }


def shuffle_pvalue(resid: np.ndarray, kappa: np.ndarray, rho: np.ndarray,
                   n: int, seed: int) -> dict:
    """Permute rho across SNe, recompute kappa*rho, re-correlate vs resid.
    Empirical two-sided p = fraction of |r_shuffled| >= |r_observed|."""
    rng = np.random.default_rng(seed)
    observed_r = stats.pearsonr(resid, kappa * rho).statistic
    observed_rho_s = stats.spearmanr(resid, kappa * rho).statistic

    r_draws = np.empty(n)
    s_draws = np.empty(n)
    idx = np.arange(len(rho))
    for i in range(n):
        rho_p = rho[rng.permutation(idx)]
        kxr = kappa * rho_p
        r_draws[i] = stats.pearsonr(resid, kxr).statistic
        s_draws[i] = stats.spearmanr(resid, kxr).statistic

    p_pearson = float((np.abs(r_draws) >= abs(observed_r)).mean())
    p_spearman = float((np.abs(s_draws) >= abs(observed_rho_s)).mean())
    return {
        "observed_pearson_r": float(observed_r),
        "observed_spearman_rho": float(observed_rho_s),
        "empirical_p_pearson": p_pearson,
        "empirical_p_spearman": p_spearman,
        "shuffles": n,
    }


def scatter(x, y, xlabel, ylabel, title, path: Path, labels=None,
            highlight=None):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhline(0, color="0.7", lw=0.8)
    ax.axvline(0, color="0.7", lw=0.8)
    ax.scatter(x, y, s=55, alpha=0.85, edgecolor="black", linewidth=0.6)
    if labels is not None:
        for xi, yi, lab in zip(x, y, labels):
            ax.annotate(lab, (xi, yi), fontsize=7, alpha=0.7,
                        xytext=(4, 3), textcoords="offset points")
    if highlight is not None:
        mask = np.asarray(highlight, dtype=bool)
        ax.scatter(np.asarray(x)[mask], np.asarray(y)[mask],
                   s=110, facecolor="none", edgecolor="crimson",
                   linewidth=1.5, label="low-density tail")
        ax.legend(loc="best", fontsize=8)
    if len(x) >= 3:
        slope, intercept, r, p, _ = stats.linregress(x, y)
        xs = np.linspace(np.min(x), np.max(x), 50)
        ax.plot(xs, slope * xs + intercept, lw=1.0, color="steelblue",
                label=f"OLS  r={r:+.3f}  p={p:.3f}")
        ax.legend(loc="best", fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    counts = pd.read_csv(COUNTS_CSV)
    feats = pd.read_csv(FEATURES_CSV)

    feats = dedupe_pantheon(feats)

    merged = feats.merge(counts[["CID", "count_1deg"]], on="CID", how="inner",
                         validate="one_to_one")

    counts_arr = merged["count_1deg"].to_numpy(dtype=float)
    merged["rho_std"] = standardize(counts_arr)
    merged["kappa_x_rho"] = merged["kappa_l64_std"].to_numpy() * merged["rho_std"].to_numpy()
    merged["abs_resid"] = merged["resid_mu"].abs()

    p20, p80 = np.percentile(counts_arr, [20, 80])
    merged["low_density_tail"] = (counts_arr < p20).astype(int)
    merged["high_density_bulk"] = (counts_arr > p80).astype(int)

    merged.to_csv(MERGED_CSV, index=False)

    resid = merged["resid_mu"].to_numpy()
    abs_resid = merged["abs_resid"].to_numpy()
    rho = merged["rho_std"].to_numpy()
    kappa = merged["kappa_l64_std"].to_numpy()
    kxr = merged["kappa_x_rho"].to_numpy()
    low_mask = merged["low_density_tail"].to_numpy().astype(bool)
    high_mask = merged["high_density_bulk"].to_numpy().astype(bool)

    pairs = [
        ("resid_mu_vs_rho_std", resid, rho),
        ("resid_mu_vs_kappa_l64_std", resid, kappa),
        ("resid_mu_vs_kappa_x_rho", resid, kxr),
        ("abs_resid_vs_rho_std", abs_resid, rho),
        ("abs_resid_vs_kappa_x_rho", abs_resid, kxr),
    ]
    summary_rows = []
    for name, a, b in pairs:
        s = pearson_spearman(a, b)
        s["pair"] = name
        summary_rows.append(s)

    shuf = shuffle_pvalue(resid, kappa, rho, n=N_SHUFFLES, seed=RNG_SEED)

    # Tail diagnostics (no global averaging; report per-bucket statistics)
    def bucket_stats(label: str, mask: np.ndarray) -> dict:
        if not mask.any():
            return {"bucket": label, "n": 0}
        r = resid[mask]
        return {
            "bucket": label,
            "n": int(mask.sum()),
            "mean_resid": float(np.mean(r)),
            "median_resid": float(np.median(r)),
            "mean_abs_resid": float(np.mean(np.abs(r))),
            "std_resid": float(np.std(r, ddof=1)) if mask.sum() > 1 else float("nan"),
        }

    buckets = [
        bucket_stats("low_density_tail (<P20)", low_mask),
        bucket_stats("middle (P20-P80)", ~(low_mask | high_mask)),
        bucket_stats("high_density_bulk (>P80)", high_mask),
    ]

    # Two-sample test: low-density tail vs the rest (abs residuals)
    if low_mask.any() and (~low_mask).any():
        tail_test = stats.mannwhitneyu(abs_resid[low_mask], abs_resid[~low_mask],
                                       alternative="greater")
        tail_t = {
            "test": "Mann-Whitney U (abs_resid: low-density tail > rest)",
            "U": float(tail_test.statistic),
            "p_one_sided": float(tail_test.pvalue),
            "n_tail": int(low_mask.sum()),
            "n_rest": int((~low_mask).sum()),
        }
    else:
        tail_t = {"test": "Mann-Whitney U", "note": "insufficient bucket"}

    summary_df = pd.DataFrame(summary_rows)[
        ["pair", "n", "pearson_r", "pearson_p", "spearman_rho", "spearman_p"]
    ]
    summary_df.to_csv(SUMMARY_CSV, index=False)

    # ---------- plots ----------
    labels = merged["CID"].tolist()
    scatter(rho, resid, "rho_std (standardized count_1deg)", "resid_mu",
            "Pantheon mu-residual vs DR9 density (rho_std)", PLOT_RHO,
            labels=labels, highlight=low_mask)
    scatter(kxr, resid, "kappa_l64_std * rho_std", "resid_mu",
            "Pantheon mu-residual vs coupled structure kappa x rho",
            PLOT_KXR_RESID, labels=labels, highlight=low_mask)
    scatter(kxr, abs_resid, "kappa_l64_std * rho_std", "|resid_mu|",
            "|residual| vs coupled structure kappa x rho",
            PLOT_KXR_ABS, labels=labels, highlight=low_mask)

    # ---------- console report ----------
    print("=" * 72)
    print("MERGED TABLE")
    print("=" * 72)
    with pd.option_context("display.width", 140, "display.max_columns", 20,
                           "display.float_format", "{:+.4f}".format):
        print(merged[["CID", "zCMB", "resid_mu", "kappa_l64_std",
                      "count_1deg", "rho_std", "kappa_x_rho",
                      "low_density_tail", "high_density_bulk"]].to_string(index=False))

    print()
    print("=" * 72)
    print(f"CORRELATIONS  (n={len(merged)})")
    print("=" * 72)
    for s in summary_rows:
        print(f"  {s['pair']:34s} "
              f"Pearson r={s['pearson_r']:+.3f} (p={s['pearson_p']:.3f})   "
              f"Spearman rho={s['spearman_rho']:+.3f} (p={s['spearman_p']:.3f})")

    print()
    print("=" * 72)
    print(f"PERMUTATION TEST  (kappa x rho_perm, {N_SHUFFLES} draws)")
    print("=" * 72)
    for k, v in shuf.items():
        print(f"  {k:28s} {v}")

    print()
    print("=" * 72)
    print("TAIL BUCKETS  (no global average; per-bucket stats)")
    print("=" * 72)
    for b in buckets:
        print(" ", b)
    print()
    print(" ", tail_t)

    print()
    print("=" * 72)
    print("CONCLUSION")
    print("=" * 72)
    rho_s = summary_rows[0]
    kxr_s = summary_rows[2]
    abs_kxr_s = summary_rows[4]
    better = abs(kxr_s["pearson_r"]) > abs(rho_s["pearson_r"])
    survives = shuf["empirical_p_pearson"] < 0.05
    tail_anom = (tail_t.get("p_one_sided", 1.0) < 0.10) if "p_one_sided" in tail_t else False
    print(f"  kappa x rho vs rho-only (|Pearson r|): "
          f"{abs(kxr_s['pearson_r']):.3f}  vs  {abs(rho_s['pearson_r']):.3f}  "
          f"-> kappa x rho {'OUTPERFORMS' if better else 'does NOT outperform'} rho alone")
    print(f"  Shuffle test empirical p (Pearson)   : {shuf['empirical_p_pearson']:.4f}  "
          f"-> signal {'SURVIVES' if survives else 'does NOT survive'} shuffling at alpha=0.05")
    print(f"  Low-density tail |resid| > rest      : "
          f"p_one_sided={tail_t.get('p_one_sided', float('nan')):.3f}  "
          f"-> tail {'IS anomalous' if tail_anom else 'is NOT anomalous'} at alpha=0.10")


if __name__ == "__main__":
    main()
