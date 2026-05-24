"""
Query additional cone radii (0.25, 3.0, 5.0 deg) for the existing 150
Pantheon+ candidates, then merge with the prior 0.5/1.0/2.0 results to
produce a 6-scale density table.
"""
from __future__ import annotations

import time
from io import StringIO
from pathlib import Path

import pandas as pd
from dl import queryClient as qc

HERE = Path(__file__).resolve().parent
IN_CSV = HERE / "pantheon_dr9_multiscale.csv"
OUT_CSV = HERE / "pantheon_dr9_multiscale6.csv"

NEW_RADII = [0.25, 3.0, 5.0]


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


def col_name(r: float) -> str:
    return f"n_{int(round(r*100)):03d}cdeg"  # 0.25 -> n_025cdeg, etc.


def main() -> None:
    df = pd.read_csv(IN_CSV)
    cols = {col_name(r): [] for r in NEW_RADII}
    t0 = time.time()
    for i, row in df.iterrows():
        for r in NEW_RADII:
            cols[col_name(r)].append(cone_count(row.RA, row.DEC, r))
        if (i + 1) % 10 == 0 or i == len(df) - 1:
            dt = time.time() - t0
            print(f"  [{i+1:3d}/{len(df)}]  {row.CID:>12s}  "
                  f"n025={cols[col_name(0.25)][-1]:>6d}  "
                  f"n300={cols[col_name(3.0)][-1]:>8d}  "
                  f"n500={cols[col_name(5.0)][-1]:>9d}   "
                  f"({dt:.1f}s elapsed)")

    out = df.copy()
    for k, v in cols.items():
        out[k] = v
    out.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {len(out)} rows -> {OUT_CSV}")


if __name__ == "__main__":
    main()
