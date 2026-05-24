"""
Spatial-graph corridor test + multi-scale density peak finder.

Input: pantheon_dr9_multiscale6.csv  (per-SN cone counts at 6 radii:
       0.25, 0.5, 1.0, 2.0, 3.0, 5.0 deg)

Pipeline:

  1. Multi-scale density features
       * log-rho at each of 6 radii
       * gradient (OLS slope of log_rho vs log_r) computed in 5 sliding
         3-scale windows -> identify radius where |grad| best predicts
         |resid_mu|
       * total-window gradient + multi-scale variance

  2. 3-D comoving spatial graph
       * comoving distance from zCMB (flat LCDM Om=0.334, H0=73.5)
       * (x,y,z) = D_C * (cos d cos a, cos d sin a, sin d)
       * mutual-kNN graph with k=8 (Euclidean in comoving 3-D)

  3. Graph corridor / neck features
       * neighbor_log_rho_mean / std
       * own_minus_neighbor (local density anomaly)
       * neighbor_high_low_pairs  (transition pairs in i's neighborhood)
       * corridor_betweenness     (BC restricted to high-density terminals)
       * graph_neck_score = z(neighbor_log_rho_std)
                          + z(neighbor_high_low_pairs)
                          + z(corridor_betweenness)

  4. Robustness battery
       * leave-one-out: drop each SN, recompute Pearson r vs |resid|;
         report observed r and full LOO range
       * bootstrap 2000 resamples, 95% CI on Pearson r
       * adversarial: 10000 permutations of node densities on the
         FIXED graph topology (preserves the graph, breaks node-density
         pairing)
       * graph-edge shuffle: 10000 degree-preserving edge swaps,
         recompute corridor_betweenness on the rewired graph, then
         re-correlate with |resid|

  5. Direct comparison
       rho_10_std | abs_grad_best_window | neck_score (scalar) |
       graph_neck_score | corridor_betweenness | neighbor_log_rho_std

Outputs:
  pantheon_dr9_topology_v2.csv
  multiscale_peak_scan.csv
  graph_summary.csv
  graph_shuffle.csv
  graph_bootstrap.csv
  graph_loo.csv
  scatter_absresid_vs_graph_neck.png
  scatter_absresid_vs_corridor_bc.png
  scatter_absresid_vs_neighbor_logrho_std.png
  scale_peak_curve.png
  graph_visualisation.png
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
from scipy.integrate import quad
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
IN_CSV = HERE / "pantheon_dr9_multiscale6.csv"
OUT_FEATS = HERE / "pantheon_dr9_topology_v2.csv"
OUT_PEAK = HERE / "multiscale_peak_scan.csv"
OUT_GSUM = HERE / "graph_summary.csv"
OUT_GSHUF = HERE / "graph_shuffle.csv"
OUT_GBOOT = HERE / "graph_bootstrap.csv"
OUT_GLOO = HERE / "graph_loo.csv"

# Pantheon+SH0ES best-fit
H0 = 73.5
OM = 0.334
C_KMS = 299_792.458
DH = C_KMS / H0   # Mpc

KNN = 8
N_SHUFFLES = 10_000          # scalar shuffles (fast)
N_GRAPH_SHUFFLES = 2_000     # density-permute + graph_features recompute
N_BOOT = 2_000
N_EDGE_SWAPS_ROUNDS = 200    # rewires; each rewire does ~|E| swaps
RNG_SEED = 20260524

RADII = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0])
RAD_COLS = ["n_025cdeg", "n_050cdeg", "n_100cdeg",
            "n_200cdeg", "n_300cdeg", "n_500cdeg"]


def comoving_distance(z: np.ndarray) -> np.ndarray:
    def E(zp): return 1.0 / np.sqrt(OM * (1 + zp) ** 3 + (1 - OM))
    return DH * np.array([quad(E, 0, zi, limit=200)[0] for zi in z])


def standardize(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    mu = np.nanmean(a)
    sd = np.nanstd(a, ddof=1)
    return (a - mu) / sd if sd > 0 else a - mu


def safe_log_density(n: np.ndarray, area: float) -> np.ndarray:
    return np.log10((n.astype(float) + 1.0) / area)


def per_sn_gradient(log_rho_mat: np.ndarray, log_r: np.ndarray) -> np.ndarray:
    x = log_r
    x_mean = x.mean()
    denom = np.sum((x - x_mean) ** 2)
    y_mean = log_rho_mat.mean(axis=1, keepdims=True)
    return np.sum((x - x_mean) * (log_rho_mat - y_mean), axis=1) / denom


def pearson_safe(x: np.ndarray, y: np.ndarray) -> tuple[float, float, int]:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan"), float("nan"), int(m.sum())
    pr = stats.pearsonr(x[m], y[m])
    return float(pr.statistic), float(pr.pvalue), int(m.sum())


def spearman_safe(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan"), float("nan")
    sr = stats.spearmanr(x[m], y[m])
    return float(sr.statistic), float(sr.pvalue)


def build_3d_positions(ra_deg: np.ndarray, dec_deg: np.ndarray,
                       z: np.ndarray) -> np.ndarray:
    ra = np.deg2rad(ra_deg)
    dec = np.deg2rad(dec_deg)
    dc = comoving_distance(z)
    x = dc * np.cos(dec) * np.cos(ra)
    y = dc * np.cos(dec) * np.sin(ra)
    z_ = dc * np.sin(dec)
    return np.column_stack([x, y, z_])


def build_mutual_knn_graph(positions: np.ndarray, k: int) -> nx.Graph:
    n = len(positions)
    tree = cKDTree(positions)
    _, idx = tree.query(positions, k=k + 1)  # +1 because each point is its own nearest neighbour
    neighbours = [set(idx[i, 1:].tolist()) for i in range(n)]
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in neighbours[i]:
            if i in neighbours[j]:
                G.add_edge(i, j)
    return G


def graph_features(G: nx.Graph, log_rho: np.ndarray,
                   p_low: float, p_high: float) -> dict:
    n = G.number_of_nodes()
    deg = np.array([G.degree(i) for i in range(n)], dtype=int)

    nbr_mean = np.full(n, np.nan)
    nbr_std = np.full(n, np.nan)
    nbr_high_low_pairs = np.zeros(n, dtype=float)
    own_minus_nbr = np.full(n, np.nan)

    for i in range(n):
        nbrs = list(G.neighbors(i))
        if not nbrs:
            continue
        vals = log_rho[nbrs]
        nbr_mean[i] = float(np.mean(vals))
        nbr_std[i] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        own_minus_nbr[i] = float(log_rho[i] - nbr_mean[i])
        high = vals > p_high
        low = vals < p_low
        nbr_high_low_pairs[i] = float(int(high.sum()) * int(low.sum()))

    # Corridor betweenness: restrict source/target set to high-density nodes.
    high_nodes = [i for i in range(n) if log_rho[i] > p_high]
    bc_dict = {i: 0.0 for i in range(n)}
    if len(high_nodes) >= 2:
        bc = nx.betweenness_centrality_subset(
            G, sources=high_nodes, targets=high_nodes, normalized=True
        )
        bc_dict.update(bc)
    corridor_bc = np.array([bc_dict.get(i, 0.0) for i in range(n)])

    return dict(
        degree=deg,
        neighbor_log_rho_mean=nbr_mean,
        neighbor_log_rho_std=nbr_std,
        own_minus_neighbor=own_minus_nbr,
        neighbor_high_low_pairs=nbr_high_low_pairs,
        corridor_betweenness=corridor_bc,
    )


def degree_preserving_swap(G: nx.Graph, rng: np.random.Generator,
                           n_swaps: int) -> nx.Graph:
    """Configuration-style double-edge swap that preserves the degree
    sequence. Falls back gracefully if the swap is infeasible."""
    H = G.copy()
    edges = list(H.edges())
    if len(edges) < 2:
        return H
    attempts = 0
    swaps = 0
    edge_array = edges
    while swaps < n_swaps and attempts < 10 * n_swaps:
        attempts += 1
        i, j = rng.integers(0, len(edge_array), size=2)
        if i == j:
            continue
        a, b = edge_array[i]
        c, d = edge_array[j]
        if len({a, b, c, d}) < 4:
            continue
        if H.has_edge(a, d) or H.has_edge(c, b):
            continue
        H.remove_edge(a, b)
        H.remove_edge(c, d)
        H.add_edge(a, d)
        H.add_edge(c, b)
        edge_array = list(H.edges())
        swaps += 1
    return H


def main() -> None:
    df = pd.read_csv(IN_CSV)
    bad = (df[RAD_COLS] < 0).any(axis=1)
    if bad.any():
        print(f"dropping {int(bad.sum())} rows with failed cone queries")
        df = df[~bad].reset_index(drop=True)

    areas = np.pi * RADII ** 2
    log_rho_per_scale = np.column_stack([
        safe_log_density(df[col].to_numpy(), area)
        for col, area in zip(RAD_COLS, areas)
    ])
    log_r = np.log(RADII)
    log_r_mean = log_r.mean()

    # ---------- (1) multi-scale density features --------------------
    abs_r = df["resid_mu"].abs().to_numpy()
    resid = df["resid_mu"].to_numpy()

    # Total-window gradient (all 6 scales)
    full_grad = per_sn_gradient(log_rho_per_scale, log_r)
    multiscale_var = log_rho_per_scale.std(axis=1, ddof=1)

    # Sliding 3-scale window gradient -> find peak scale
    peak_rows = []
    sliding_grads = {}
    for k in range(len(RADII) - 2):
        sub_r = log_r[k:k + 3]
        sub_lr = log_rho_per_scale[:, k:k + 3]
        g = per_sn_gradient(sub_lr, sub_r)
        sliding_grads[f"grad_{RADII[k]:.2f}-{RADII[k+2]:.2f}deg"] = g
        rp, pp, npts = pearson_safe(np.abs(g), abs_r)
        sp, sp_p = spearman_safe(np.abs(g), abs_r)
        center = float(np.exp(np.mean(np.log(RADII[k:k + 3]))))
        peak_rows.append({
            "window_low_deg": float(RADII[k]),
            "window_high_deg": float(RADII[k + 2]),
            "window_center_deg": center,
            "n": npts,
            "pearson_r_absgrad_vs_absresid": rp,
            "pearson_p": pp,
            "spearman_rho": sp,
            "spearman_p": sp_p,
        })
    peak_df = pd.DataFrame(peak_rows)
    peak_df.to_csv(OUT_PEAK, index=False)
    best = peak_df.iloc[peak_df["pearson_r_absgrad_vs_absresid"].abs().idxmax()]
    best_key = (f"grad_{best.window_low_deg:.2f}-{best.window_high_deg:.2f}deg")
    best_grad = sliding_grads[best_key]

    # ---------- (2) 3-D comoving graph ------------------------------
    positions = build_3d_positions(df["RA"].to_numpy(),
                                   df["DEC"].to_numpy(),
                                   df["zCMB"].to_numpy())
    G = build_mutual_knn_graph(positions, k=KNN)

    log_rho_1deg = log_rho_per_scale[:, 2]  # n_100cdeg corresponds to 1 deg
    p_low, p_high = np.percentile(log_rho_1deg, [33, 67])

    gf = graph_features(G, log_rho_1deg, p_low, p_high)

    graph_neck_score = (standardize(gf["neighbor_log_rho_std"])
                        + standardize(gf["neighbor_high_low_pairs"])
                        + standardize(gf["corridor_betweenness"]))

    # ---------- assemble feature table ------------------------------
    out = df.copy()
    for i, col in enumerate(["log_rho_025", "log_rho_050", "log_rho_100",
                             "log_rho_200", "log_rho_300", "log_rho_500"]):
        out[col] = log_rho_per_scale[:, i]
    out["rho_100_std"] = standardize(log_rho_per_scale[:, 2])
    out["full_grad_logrho_logr"] = full_grad
    out["abs_full_grad"] = np.abs(full_grad)
    out["multiscale_var"] = multiscale_var
    for k, v in sliding_grads.items():
        out[k] = v
        out[f"abs_{k}"] = np.abs(v)
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

    out.to_csv(OUT_FEATS, index=False)

    # ---------- (3) correlations & comparison -----------------------
    test_features = {
        "rho_100_std": out["rho_100_std"].to_numpy(),
        "abs_full_grad": out["abs_full_grad"].to_numpy(),
        "best_window_abs_grad": out["best_window_abs_grad"].to_numpy(),
        "multiscale_var": out["multiscale_var"].to_numpy(),
        "neighbor_log_rho_std": out["neighbor_log_rho_std"].to_numpy(),
        "abs_own_minus_neighbor": out["abs_own_minus_neighbor"].to_numpy(),
        "neighbor_high_low_pairs": out["neighbor_high_low_pairs"].to_numpy(),
        "corridor_betweenness": out["corridor_betweenness"].to_numpy(),
        "graph_neck_score": out["graph_neck_score"].to_numpy(),
    }
    corr_rows = []
    for name, x in test_features.items():
        for target_name, target in [("resid_mu", resid), ("abs_resid", abs_r)]:
            r, p, n = pearson_safe(x, target)
            sr, sp = spearman_safe(x, target)
            corr_rows.append({"feature": name, "target": target_name, "n": n,
                              "pearson_r": r, "pearson_p": p,
                              "spearman_rho": sr, "spearman_p": sp})
    pd.DataFrame(corr_rows).to_csv(OUT_GSUM, index=False)

    # ---------- (4a) leave-one-out --------------------------------
    loo_rows = []
    for name, x in test_features.items():
        loo_rs = []
        for i in range(len(x)):
            mask = np.ones_like(x, dtype=bool)
            mask[i] = False
            r, _, _ = pearson_safe(x[mask], abs_r[mask])
            loo_rs.append(r)
        loo_rs = np.array(loo_rs)
        observed_r, observed_p, _ = pearson_safe(x, abs_r)
        loo_rows.append({
            "feature": name,
            "observed_r_vs_abs_resid": observed_r,
            "observed_p": observed_p,
            "loo_r_min": float(np.nanmin(loo_rs)),
            "loo_r_max": float(np.nanmax(loo_rs)),
            "loo_r_median": float(np.nanmedian(loo_rs)),
            "loo_r_std": float(np.nanstd(loo_rs)),
        })
    pd.DataFrame(loo_rows).to_csv(OUT_GLOO, index=False)

    # ---------- (4b) bootstrap CI ---------------------------------
    rng = np.random.default_rng(RNG_SEED)
    boot_rows = []
    n = len(abs_r)
    for name, x in test_features.items():
        rs = np.empty(N_BOOT)
        for b in range(N_BOOT):
            idx = rng.integers(0, n, size=n)
            rs[b] = pearson_safe(x[idx], abs_r[idx])[0]
        rs = rs[np.isfinite(rs)]
        boot_rows.append({
            "feature": name,
            "observed_r": pearson_safe(x, abs_r)[0],
            "boot_mean": float(np.mean(rs)),
            "boot_median": float(np.median(rs)),
            "ci2_5": float(np.percentile(rs, 2.5)),
            "ci97_5": float(np.percentile(rs, 97.5)),
            "n_boot": int(len(rs)),
        })
    pd.DataFrame(boot_rows).to_csv(OUT_GBOOT, index=False)

    # ---------- (4c) shuffle node densities on fixed graph -------
    shuf_rows = []
    # For graph-derived features we re-derive them from shuffled densities.
    for name in ["neighbor_log_rho_std", "neighbor_high_low_pairs",
                 "corridor_betweenness", "graph_neck_score"]:
        observed = test_features[name]
        observed_r, _, _ = pearson_safe(observed, abs_r)
        draws = np.empty(N_GRAPH_SHUFFLES)
        for it in range(N_GRAPH_SHUFFLES):
            perm = rng.permutation(n)
            lr_p = log_rho_1deg[perm]
            gf_p = graph_features(G, lr_p, p_low, p_high)
            if name == "graph_neck_score":
                gn = (standardize(gf_p["neighbor_log_rho_std"])
                      + standardize(gf_p["neighbor_high_low_pairs"])
                      + standardize(gf_p["corridor_betweenness"]))
                draws[it] = pearson_safe(gn, abs_r)[0]
            else:
                draws[it] = pearson_safe(gf_p[name], abs_r)[0]
        p_emp = float((np.abs(draws[np.isfinite(draws)]) >= abs(observed_r)).mean())
        shuf_rows.append({
            "feature": name,
            "observed_r_vs_abs_resid": observed_r,
            "test": "permute node densities on fixed graph",
            "n_shuffles": N_GRAPH_SHUFFLES,
            "empirical_p_two_sided": p_emp,
        })

    # ---------- (4d) degree-preserving edge swap -----------------
    # Rewire the graph keeping degrees fixed; recompute corridor BC + neck.
    observed_bc = gf["corridor_betweenness"]
    observed_bc_r, _, _ = pearson_safe(observed_bc, abs_r)
    observed_neck = graph_neck_score
    observed_neck_r, _, _ = pearson_safe(observed_neck, abs_r)
    bc_draws = np.empty(N_EDGE_SWAPS_ROUNDS)
    neck_draws = np.empty(N_EDGE_SWAPS_ROUNDS)
    for it in range(N_EDGE_SWAPS_ROUNDS):
        H = degree_preserving_swap(G, rng, n_swaps=max(50, G.number_of_edges()))
        gf_h = graph_features(H, log_rho_1deg, p_low, p_high)
        bc_draws[it] = pearson_safe(gf_h["corridor_betweenness"], abs_r)[0]
        gn = (standardize(gf_h["neighbor_log_rho_std"])
              + standardize(gf_h["neighbor_high_low_pairs"])
              + standardize(gf_h["corridor_betweenness"]))
        neck_draws[it] = pearson_safe(gn, abs_r)[0]

    shuf_rows.append({
        "feature": "corridor_betweenness",
        "observed_r_vs_abs_resid": observed_bc_r,
        "test": f"degree-preserving edge swap ({N_EDGE_SWAPS_ROUNDS} rewires)",
        "n_shuffles": N_EDGE_SWAPS_ROUNDS,
        "empirical_p_two_sided": float((np.abs(bc_draws[np.isfinite(bc_draws)]) >= abs(observed_bc_r)).mean()),
    })
    shuf_rows.append({
        "feature": "graph_neck_score",
        "observed_r_vs_abs_resid": observed_neck_r,
        "test": f"degree-preserving edge swap ({N_EDGE_SWAPS_ROUNDS} rewires)",
        "n_shuffles": N_EDGE_SWAPS_ROUNDS,
        "empirical_p_two_sided": float((np.abs(neck_draws[np.isfinite(neck_draws)]) >= abs(observed_neck_r)).mean()),
    })

    pd.DataFrame(shuf_rows).to_csv(OUT_GSHUF, index=False)

    # ---------- plots --------------------------------------------
    def scat(x, y, xlab, ylab, title, path):
        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.scatter(x, y, s=24, alpha=0.8, edgecolor="black", linewidth=0.3)
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() >= 3:
            slope, intercept, rr, pp, _ = stats.linregress(x[m], y[m])
            xs = np.linspace(np.nanmin(x), np.nanmax(x), 50)
            ax.plot(xs, slope * xs + intercept, color="steelblue", lw=1,
                    label=f"OLS r={rr:+.3f}  p={pp:.3g}")
        ax.set_xlabel(xlab); ax.set_ylabel(ylab); ax.set_title(title)
        ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(path, dpi=140)
        plt.close(fig)

    scat(out["graph_neck_score"].to_numpy(), abs_r,
         "graph_neck_score", "|resid_mu|",
         f"|residual| vs graph-based neck score  (n={len(out)})",
         HERE / "scatter_absresid_vs_graph_neck.png")
    scat(out["corridor_betweenness"].to_numpy(), abs_r,
         "corridor_betweenness (BC across high-density terminals)",
         "|resid_mu|",
         f"|residual| vs corridor betweenness  (n={len(out)})",
         HERE / "scatter_absresid_vs_corridor_bc.png")
    scat(out["neighbor_log_rho_std"].to_numpy(), abs_r,
         "std(log rho) across mutual-kNN neighbours",
         "|resid_mu|",
         f"|residual| vs kNN log-density std  (n={len(out)})",
         HERE / "scatter_absresid_vs_neighbor_logrho_std.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    centers = peak_df["window_center_deg"].to_numpy()
    rs = peak_df["pearson_r_absgrad_vs_absresid"].to_numpy()
    ax.axhline(0, color="0.75", lw=0.6)
    ax.plot(centers, rs, "o-", color="darkorange")
    for ci, ri, lo, hi in zip(centers, rs, peak_df["window_low_deg"],
                              peak_df["window_high_deg"]):
        ax.annotate(f"{lo:g}-{hi:g}°", (ci, ri), fontsize=8,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("window centre (deg, geometric mean)")
    ax.set_ylabel("Pearson r(|abs_grad|, |resid_mu|)")
    ax.set_title("multi-scale gradient: which window predicts |resid| best?")
    fig.tight_layout(); fig.savefig(HERE / "scale_peak_curve.png", dpi=140)
    plt.close(fig)

    # Graph visualisation (2-D projection: RA vs DEC, colour by log_rho_1deg)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    pos = {i: (df["RA"].iloc[i], df["DEC"].iloc[i]) for i in range(len(df))}
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.25, width=0.5)
    sc = ax.scatter(df["RA"], df["DEC"], c=log_rho_1deg, cmap="viridis",
                    s=20 + 80 * standardize(abs_r) * (abs_r > np.median(abs_r)),
                    edgecolor="black", linewidth=0.3)
    plt.colorbar(sc, ax=ax, label="log rho (1 deg)")
    ax.set_xlabel("RA (deg)"); ax.set_ylabel("DEC (deg)")
    ax.set_title(f"mutual-kNN (k={KNN}) graph; marker size scales with |resid|")
    fig.tight_layout(); fig.savefig(HERE / "graph_visualisation.png", dpi=140)
    plt.close(fig)

    # ---------- console summary ---------------------------------
    print("=" * 78)
    print(f"GRAPH n={G.number_of_nodes()}  edges={G.number_of_edges()}  "
          f"k={KNN}  components={nx.number_connected_components(G)}")
    print("=" * 78)
    print()
    print("MULTI-SCALE GRADIENT PEAK SCAN")
    print(peak_df.to_string(index=False, float_format="{:+.4f}".format))
    print(f"  -> best window: {best_key}  r={best.pearson_r_absgrad_vs_absresid:+.3f}")
    print()
    print("CORRELATIONS vs |resid_mu|")
    abs_corr_rows = [r for r in corr_rows if r["target"] == "abs_resid"]
    for r in abs_corr_rows:
        print(f"  {r['feature']:24s}  r={r['pearson_r']:+.3f}  "
              f"p={r['pearson_p']:.3g}   "
              f"rho_s={r['spearman_rho']:+.3f}  p_s={r['spearman_p']:.3g}")
    print()
    print("BOOTSTRAP 95% CI (vs |resid|)")
    for row in boot_rows:
        print(f"  {row['feature']:24s}  r={row['observed_r']:+.3f}  "
              f"CI[{row['ci2_5']:+.3f}, {row['ci97_5']:+.3f}]")
    print()
    print("LEAVE-ONE-OUT (vs |resid|)")
    for row in loo_rows:
        print(f"  {row['feature']:24s}  r={row['observed_r_vs_abs_resid']:+.3f}  "
              f"LOO range [{row['loo_r_min']:+.3f}, {row['loo_r_max']:+.3f}]")
    print()
    print("ADVERSARIAL")
    for row in shuf_rows:
        print(f"  {row['feature']:24s}  obs r={row['observed_r_vs_abs_resid']:+.3f}  "
              f"emp p={row['empirical_p_two_sided']:.4f}  [{row['test']}]")


if __name__ == "__main__":
    main()
