"""
Pull RA/DEC/zCMB/MU_SH0ES from the Pantheon+ public release, drop
calibrators and very-low-z anchors, compute flat-LCDM residuals
mu_obs - mu_model, restrict to the DR9 sky band, and emit a
deterministic candidate list of ~150 SNe (target N>=100 after DR9
footprint losses).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import quad

HERE = Path(__file__).resolve().parent
RAW = Path("/tmp/PantheonPlusSH0ES.dat")
OUT = HERE / "pantheon_candidates.csv"

# Pantheon+SH0ES best-fit (Brout+22 Table 3, w=-1)
H0 = 73.5
OM = 0.334
C_KMS = 299_792.458


def mu_model(z: np.ndarray) -> np.ndarray:
    def E(zp): return 1.0 / np.sqrt(OM * (1 + zp) ** 3 + (1 - OM))
    dC = np.array([quad(E, 0, zi, limit=200)[0] for zi in z])  # in units of c/H0
    dL_Mpc = (C_KMS / H0) * (1 + z) * dC
    return 5 * np.log10(dL_Mpc) + 25


def main() -> None:
    df = pd.read_csv(RAW, sep=r"\s+")
    df = df[(df["IS_CALIBRATOR"] == 0)
            & (df["zCMB"] > 0.01)
            & (df["DEC"] > -20.0)  # rough DR9 southern edge
            & (df["DEC"] < 80.0)
            & (df["MU_SH0ES"] > 0)
            & (df["MU_SH0ES_ERR_DIAG"] > 0)].copy()
    df = df.drop_duplicates(subset="CID", keep="first")

    df["mu_model"] = mu_model(df["zCMB"].to_numpy())
    df["resid_mu"] = df["MU_SH0ES"].to_numpy() - df["mu_model"].to_numpy()
    df["resid_mu_err"] = df["MU_SH0ES_ERR_DIAG"].to_numpy()

    # Deterministic 150-sample: stable hash of CID, take smallest 150.
    df["_h"] = df["CID"].astype(str).map(lambda s: int.from_bytes(s.encode(), "little") % (10 ** 9))
    df = df.sort_values("_h").head(150).drop(columns="_h")
    df = df.sort_values("CID").reset_index(drop=True)

    out = df[["CID", "RA", "DEC", "zCMB", "MU_SH0ES",
              "MU_SH0ES_ERR_DIAG", "mu_model", "resid_mu", "resid_mu_err"]]
    out.to_csv(OUT, index=False)
    print(f"wrote {len(out)} candidates -> {OUT}")
    print(f"DEC range: [{out.DEC.min():.2f}, {out.DEC.max():.2f}]")
    print(f"z range:   [{out.zCMB.min():.4f}, {out.zCMB.max():.4f}]")
    print(f"resid_mu:  mean={out.resid_mu.mean():+.4f}  std={out.resid_mu.std():.4f}")


if __name__ == "__main__":
    main()
