"""
Graph-corridor + multi-scale analysis on the N=400 expanded Pantheon+ x DR9
sample.

Input:  pantheon_dr9_grid_400.csv  (6 cone radii, consistent column names)
Output: *_n400.csv / *_n400.png mirroring the n=150 outputs.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats

import analyze_graph_corridor as base

HERE = Path(__file__).resolve().parent
IN_CSV = HERE / "pantheon_dr9_grid_400.csv"

RADII = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0])
RAD_COLS = ["n_025cdeg", "n_050cdeg", "n_100cdeg",
            "n_200cdeg", "n_300cdeg", "n_500cdeg"]

KNN = 8
N_SHUFFLES_SCALAR = 10_000
N_GRAPH_SHUFFLES = 1_000      # 4x feature reuse per shuffle
N_BOOT = 2_000
N_EDGE_SWAPS_ROUNDS = 100
RNG_SEED = 20260524


def main() -> None:
    df = pd.read_csv(IN_CSV)
    bad = (df[RAD_COLS] < 0).any(axis=1)
    if bad.any():
        print(f"dropping {int(bad.sum())} rows with failed cone queries")
        df = df[~bad].reset_index(drop=True)

    areas = np.pi * RADII ** 2
    log_rho = np.column_stack([base.safe_log_density(df[c].to_numpy(), a)
                               for c, a in zip(RAD_COLS, areas)])
    log_r = np.log(RADII)

    resid = df["resid_mu"].to_numpy()
    abs_r = np.abs(resid)

    full_grad = base.per_sn_gradient(log_rho, log_r)
    multiscale_var = log_rho.std(axis=1, ddof=1)

    peak_rows = []
    sliding = {}
    for k in range(len(RADII) - 2):
        sub_r = log_r[k:k + 3]
        sub = log_rho[:, k:k + 3]
        g = base.per_sn_gradient(sub, sub_r)
        key = f"grad_{RADII[k]:.2f}-{RADII[k+2]:.2f}deg"
        sliding[key] = g
        rp, pp, n = base.pearson_safe(np.abs(g), abs_r)
        sp, sp_p = base.spearman_safe(np.abs(g), abs_r)
        peak_rows.append({
            "window_low_deg": float(RADII[k]),
            "window_high_deg": float(RADII[k + 2]),
            "window_center_deg": float(np.exp(np.mean(np.log(RADII[k:k + 3])))),
            "n": n, "pearson_r": rp, "pearson_p": pp,
            "spearman_rho": sp, "spearman_p": sp_p,
        })
    peak_df = pd.DataFrame(peak_rows)
    peak_df.to_csv(HERE / "multiscale_peak_scan_n400.csv", index=False)
    best_idx = peak_df["pearson_r"].abs().idxmax()
    best_key = (f"grad_{peak_df.iloc[best_idx].window_low_deg:.2f}-"
                f"{peak_df.iloc[best_idx].window_high_deg:.2f}deg")
    best_grad = sliding[best_key]

    pos = base.build_3d_positions(df["RA"].to_numpy(),
                                  df["DEC"].to_numpy(),
                                  df["zCMB"].to_numpy())
    G = base.build_mutual_knn_graph(pos, KNN)
    log_rho_1deg = log_rho[:, 2]
    p_low, p_high = np.percentile(log_rho_1deg, [33, 67])
    gf = base.graph_features(G, log_rho_1deg, p_low, p_high)

    graph_neck_score = (base.standardize(gf["neighbor_log_rho_std"])
                        + base.standardize(gf["neighbor_high_low_pairs"])
                        + base.standardize(gf["corridor_betweenness"]))

    out = df.copy()
    for i, col in enumerate(["log_rho_025", "log_rho_050", "log_rho_100",
                             "log_rho_200", "log_rho_300", "log_rho_500"]):
        out[col] = log_rho[:, i]
    out["rho_100_std"] = base.standardize(log_rho[:, 2])
    out["full_grad_logrho_logr"] = full_grad
    out["abs_full_grad"] = np.abs(full_grad)
    out["multiscale_var"] = multiscale_var
    out["best_window_abs_grad"] = np.abs(best_grad)
    out["graph_degree"] = gf["degree"]
    out["neighbor_log_rho_mean"] = gf["neighbor_log_rho_mean"]
    out["neighbor_log_rho_std"] = gf["neighbor_log_rho_std"]
    out["own_minus_neighbor"] = gf["own_minus_neighbor"]
    out["abs_own_minus_neighbor"] = np.abs(gf["own_minus_neighbor"])
    out["neighbor_high_low_pairs"] = gf["neighbor_high_low_pairs"]
    out["corridor_betweenness"] = gf["corridor_betweenness"]
    out["graph_neck_score"] = graph_neck_score
    out["abs_resid"] = abs_r
    out.to_csv(HERE / "pantheon_dr9_topology_v2_n400.csv", index=False)

    test = {
        "rho_100_std": out["rho_100_std"].to_numpy(),
        "abs_full_grad": np.abs(full_grad),
        "best_window_abs_grad": np.abs(best_grad),
        "multiscale_var": multiscale_var,
        "neighbor_log_rho_std": gf["neighbor_log_rho_std"],
        "abs_own_minus_neighbor": np.abs(gf["own_minus_neighbor"]),
        "neighbor_high_low_pairs": gf["neighbor_high_low_pairs"],
        "corridor_betweenness": gf["corridor_betweenness"],
        "graph_neck_score": graph_neck_score,
    }
    corr_rows = []
    for name, x in test.items():
        for tname, t in [("resid_mu", resid), ("abs_resid", abs_r)]:
            r, p, n = base.pearson_safe(x, t)
            sr, sp = base.spearman_safe(x, t)
            corr_rows.append({"feature": name, "target": tname, "n": n,
                              "pearson_r": r, "pearson_p": p,
                              "spearman_rho": sr, "spearman_p": sp})
    pd.DataFrame(corr_rows).to_csv(HERE / "graph_summary_n400.csv", index=False)

    # leave-one-out
    loo_rows = []
    for name, x in test.items():
        loo = []
        for i in range(len(x)):
            m = np.ones_like(x, dtype=bool); m[i] = False
            loo.append(base.pearson_safe(x[m], abs_r[m])[0])
        loo = np.array(loo)
        obs_r, obs_p, _ = base.pearson_safe(x, abs_r)
        loo_rows.append({
            "feature": name, "observed_r": obs_r, "observed_p": obs_p,
            "loo_min": float(np.nanmin(loo)), "loo_max": float(np.nanmax(loo)),
            "loo_median": float(np.nanmedian(loo)),
        })
    pd.DataFrame(loo_rows).to_csv(HERE / "graph_loo_n400.csv", index=False)

    # bootstrap
    rng = np.random.default_rng(RNG_SEED)
    n = len(abs_r)
    boot_rows = []
    for name, x in test.items():
        rs = np.empty(N_BOOT)
        for b in range(N_BOOT):
            idx = rng.integers(0, n, size=n)
            rs[b] = base.pearson_safe(x[idx], abs_r[idx])[0]
        rs = rs[np.isfinite(rs)]
        boot_rows.append({
            "feature": name, "observed_r": base.pearson_safe(x, abs_r)[0],
            "boot_mean": float(np.mean(rs)),
            "ci2_5": float(np.percentile(rs, 2.5)),
            "ci97_5": float(np.percentile(rs, 97.5)),
            "n_boot": int(len(rs)),
        })
    pd.DataFrame(boot_rows).to_csv(HERE / "graph_bootstrap_n400.csv", index=False)

    # adversarial: density permutation on fixed graph -- compute all
    # features ONCE per permutation, not per feature.
    shuf_rows = []
    feat_names = ["neighbor_log_rho_std", "neighbor_high_low_pairs",
                  "corridor_betweenness", "graph_neck_score"]
    observed_r = {name: base.pearson_safe(test[name], abs_r)[0] for name in feat_names}
    draws = {name: np.empty(N_GRAPH_SHUFFLES) for name in feat_names}
    print(f"  density permutation: {N_GRAPH_SHUFFLES} shuffles on n={n} graph...")
    import time as _time
    t0 = _time.time()
    for it in range(N_GRAPH_SHUFFLES):
        perm = rng.permutation(n)
        gp = base.graph_features(G, log_rho_1deg[perm], p_low, p_high)
        gn = (base.standardize(gp["neighbor_log_rho_std"])
              + base.standardize(gp["neighbor_high_low_pairs"])
              + base.standardize(gp["corridor_betweenness"]))
        draws["neighbor_log_rho_std"][it] = base.pearson_safe(gp["neighbor_log_rho_std"], abs_r)[0]
        draws["neighbor_high_low_pairs"][it] = base.pearson_safe(gp["neighbor_high_low_pairs"], abs_r)[0]
        draws["corridor_betweenness"][it] = base.pearson_safe(gp["corridor_betweenness"], abs_r)[0]
        draws["graph_neck_score"][it] = base.pearson_safe(gn, abs_r)[0]
        if (it + 1) % 100 == 0:
            dt = _time.time() - t0
            print(f"    [{it+1}/{N_GRAPH_SHUFFLES}]  {dt:.1f}s elapsed  "
                  f"({dt/(it+1):.2f}s/shuffle)")
    for name in feat_names:
        d = draws[name][np.isfinite(draws[name])]
        shuf_rows.append({
            "feature": name, "observed_r": observed_r[name],
            "test": "density permutation on fixed graph",
            "n_shuffles": N_GRAPH_SHUFFLES,
            "empirical_p": float((np.abs(d) >= abs(observed_r[name])).mean()),
        })

    # edge swap
    observed_bc = gf["corridor_betweenness"]
    obs_bc_r, _, _ = base.pearson_safe(observed_bc, abs_r)
    obs_neck_r, _, _ = base.pearson_safe(graph_neck_score, abs_r)
    bc_draws = np.empty(N_EDGE_SWAPS_ROUNDS)
    neck_draws = np.empty(N_EDGE_SWAPS_ROUNDS)
    for it in range(N_EDGE_SWAPS_ROUNDS):
        H = base.degree_preserving_swap(G, rng,
                                        n_swaps=max(50, G.number_of_edges()))
        gph = base.graph_features(H, log_rho_1deg, p_low, p_high)
        bc_draws[it] = base.pearson_safe(gph["corridor_betweenness"], abs_r)[0]
        gn = (base.standardize(gph["neighbor_log_rho_std"])
              + base.standardize(gph["neighbor_high_low_pairs"])
              + base.standardize(gph["corridor_betweenness"]))
        neck_draws[it] = base.pearson_safe(gn, abs_r)[0]

    shuf_rows.append({
        "feature": "corridor_betweenness", "observed_r": obs_bc_r,
        "test": f"degree-preserving edge swap ({N_EDGE_SWAPS_ROUNDS})",
        "n_shuffles": N_EDGE_SWAPS_ROUNDS,
        "empirical_p": float((np.abs(bc_draws[np.isfinite(bc_draws)]) >= abs(obs_bc_r)).mean()),
    })
    shuf_rows.append({
        "feature": "graph_neck_score", "observed_r": obs_neck_r,
        "test": f"degree-preserving edge swap ({N_EDGE_SWAPS_ROUNDS})",
        "n_shuffles": N_EDGE_SWAPS_ROUNDS,
        "empirical_p": float((np.abs(neck_draws[np.isfinite(neck_draws)]) >= abs(obs_neck_r)).mean()),
    })
    pd.DataFrame(shuf_rows).to_csv(HERE / "graph_shuffle_n400.csv", index=False)

    # ---------- plots ----------
    def scat(x, y, xlab, ylab, title, path):
        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.scatter(x, y, s=14, alpha=0.7, edgecolor="black", linewidth=0.2)
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() >= 3:
            slope, intercept, rr, pp, _ = stats.linregress(x[m], y[m])
            xs = np.linspace(np.nanmin(x), np.nanmax(x), 60)
            ax.plot(xs, slope * xs + intercept, color="steelblue", lw=1,
                    label=f"OLS r={rr:+.3f}  p={pp:.3g}")
        ax.set_xlabel(xlab); ax.set_ylabel(ylab); ax.set_title(title)
        ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(path, dpi=140)
        plt.close(fig)

    scat(graph_neck_score, abs_r, "graph_neck_score", "|resid_mu|",
         f"|residual| vs graph_neck_score  (n={n})",
         HERE / "scatter_absresid_vs_graph_neck_n400.png")
    scat(gf["neighbor_log_rho_std"], abs_r,
         "std(log rho) across kNN", "|resid_mu|",
         f"|residual| vs neighbor_log_rho_std  (n={n})",
         HERE / "scatter_absresid_vs_neighbor_logrho_std_n400.png")
    scat(gf["neighbor_high_low_pairs"], abs_r,
         "#(high) x #(low) neighbours", "|resid_mu|",
         f"|residual| vs neighbor_high_low_pairs  (n={n})",
         HERE / "scatter_absresid_vs_high_low_pairs_n400.png")
    scat(out["rho_100_std"].to_numpy(), abs_r,
         "rho_100_std (1-deg standardized log density)", "|resid_mu|",
         f"|residual| vs scalar density  (n={n})",
         HERE / "scatter_absresid_vs_rho_n400.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    centers = peak_df["window_center_deg"].to_numpy()
    rs = peak_df["pearson_r"].to_numpy()
    ax.axhline(0, color="0.75", lw=0.6)
    ax.plot(centers, rs, "o-", color="darkorange")
    for ci, ri, lo, hi in zip(centers, rs, peak_df["window_low_deg"],
                              peak_df["window_high_deg"]):
        ax.annotate(f"{lo:g}-{hi:g}°", (ci, ri), fontsize=8,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("window centre (deg, geometric mean)")
    ax.set_ylabel("Pearson r(|abs_grad|, |resid_mu|)")
    ax.set_title(f"gradient peak scan  n={n}")
    fig.tight_layout(); fig.savefig(HERE / "scale_peak_curve_n400.png", dpi=140)
    plt.close(fig)

    # ---------- report ----------
    print("=" * 78)
    print(f"GRAPH n={G.number_of_nodes()}  edges={G.number_of_edges()}  "
          f"k={KNN}  components={nx.number_connected_components(G)}")
    print("=" * 78)
    print("\nMULTI-SCALE GRADIENT PEAK SCAN")
    print(peak_df.to_string(index=False, float_format="{:+.4f}".format))
    print(f"  -> best window: {best_key}")
    print("\nCORRELATIONS vs |resid_mu|")
    for r in corr_rows:
        if r["target"] != "abs_resid":
            continue
        print(f"  {r['feature']:24s}  r={r['pearson_r']:+.3f}  "
              f"p={r['pearson_p']:.3g}   "
              f"rho_s={r['spearman_rho']:+.3f}  p_s={r['spearman_p']:.3g}")
    print("\nBOOTSTRAP 95% CI vs |resid|")
    for row in boot_rows:
        print(f"  {row['feature']:24s}  r={row['observed_r']:+.3f}  "
              f"CI[{row['ci2_5']:+.3f}, {row['ci97_5']:+.3f}]")
    print("\nLEAVE-ONE-OUT vs |resid|")
    for row in loo_rows:
        print(f"  {row['feature']:24s}  r={row['observed_r']:+.3f}  "
              f"LOO[{row['loo_min']:+.3f}, {row['loo_max']:+.3f}]")
    print("\nADVERSARIAL")
    for row in shuf_rows:
        print(f"  {row['feature']:24s}  obs r={row['observed_r']:+.3f}  "
              f"emp p={row['empirical_p']:.4f}  [{row['test']}]")


if __name__ == "__main__":
    main()
