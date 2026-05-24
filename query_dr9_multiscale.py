"""
For each Pantheon+ candidate, query ls_dr9.tractor cone counts at
three radii (0.5, 1.0, 2.0 degrees) with flux_r>0 AND flux_z>0.
Output one row per SN with counts at each scale. Failed queries
retry once; persistent failures are recorded as NaN.
"""
from __future__ import annotations

import time
from io import StringIO
from pathlib import Path

import pandas as pd
from dl import queryClient as qc

HERE = Path(__file__).resolve().parent
IN_CSV = HERE / "pantheon_candidates.csv"
OUT_CSV = HERE / "pantheon_dr9_multiscale.csv"

RADII = [0.5, 1.0, 2.0]


def cone_count(ra: float, dec: float, r: float) -> int:
    sql = (
        "SELECT COUNT(*) AS n FROM ls_dr9.tractor "
        f"WHERE q3c_radial_query(ra, dec, {ra}, {dec}, {r}) "
        "AND flux_r > 0 AND flux_z > 0"
    )
    for attempt in range(2):
        try:
            out = qc.query(sql=sql, fmt="csv")
            return int(pd.read_csv(StringIO(out))["n"].iloc[0])
        except Exception as exc:  # noqa: BLE001
            if attempt == 0:
                time.sleep(2.0)
                continue
            print(f"  ! failed (ra={ra}, dec={dec}, r={r}): {exc}")
            return -1


def main() -> None:
    cand = pd.read_csv(IN_CSV)
    cols = {f"n_{int(r*10):02d}deg": [] for r in RADII}
    t0 = time.time()
    for i, row in cand.iterrows():
        counts = {}
        for r in RADII:
            counts[f"n_{int(r*10):02d}deg"] = cone_count(row.RA, row.DEC, r)
        for k, v in counts.items():
            cols[k].append(v)
        if (i + 1) % 10 == 0 or i == len(cand) - 1:
            dt = time.time() - t0
            print(f"  [{i+1:3d}/{len(cand)}]  {row.CID:>12s}  "
                  f"n05={counts['n_05deg']:>7d}  n10={counts['n_10deg']:>7d}  "
                  f"n20={counts['n_20deg']:>7d}   ({dt:.1f}s elapsed)")

    out = cand.copy()
    for k, v in cols.items():
        out[k] = v
    out.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {len(out)} rows -> {OUT_CSV}")
    in_footprint = (out["n_10deg"] > 0)
    print(f"in DR9 footprint (n_10deg>0): {in_footprint.sum()}/{len(out)}")


if __name__ == "__main__":
    main()
