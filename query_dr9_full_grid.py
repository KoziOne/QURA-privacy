"""
Query DR9 cone counts at 6 radii (0.25, 0.5, 1, 2, 3, 5 deg) for an
arbitrary candidate CSV. Resumable: skips CIDs already present in the
output CSV.
"""
from __future__ import annotations

import sys
import time
from io import StringIO
from pathlib import Path

import pandas as pd
from dl import queryClient as qc

HERE = Path(__file__).resolve().parent
DEFAULT_IN = HERE / "pantheon_candidates_400.csv"
DEFAULT_OUT = HERE / "pantheon_dr9_grid_400.csv"

RADII = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0]
COL = {0.25: "n_025cdeg", 0.5: "n_050cdeg", 1.0: "n_100cdeg",
       2.0: "n_200cdeg", 3.0: "n_300cdeg", 5.0: "n_500cdeg"}


def cone_count(ra: float, dec: float, r: float) -> int:
    sql = ("SELECT COUNT(*) AS n FROM ls_dr9.tractor "
           f"WHERE q3c_radial_query(ra, dec, {ra}, {dec}, {r}) "
           "AND flux_r > 0 AND flux_z > 0")
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
    in_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    cand = pd.read_csv(in_csv)

    done = set()
    if out_csv.exists():
        prior = pd.read_csv(out_csv)
        done = set(prior["CID"].astype(str))
        print(f"resuming: {len(done)} CIDs already in {out_csv.name}")
        cand = cand[~cand["CID"].astype(str).isin(done)].reset_index(drop=True)

    t0 = time.time()
    new_rows = []
    for i, row in cand.iterrows():
        rec = {c: row[c] for c in cand.columns}
        for r in RADII:
            rec[COL[r]] = cone_count(row.RA, row.DEC, r)
        new_rows.append(rec)
        if (i + 1) % 10 == 0 or i == len(cand) - 1:
            dt = time.time() - t0
            print(f"  [{i+1:3d}/{len(cand)}]  {row.CID:>12s}  "
                  f"n025={rec[COL[0.25]]:>6d}  "
                  f"n100={rec[COL[1.0]]:>7d}  "
                  f"n500={rec[COL[5.0]]:>9d}   ({dt:.1f}s)")
            # incremental persist every 10 SNe
            inc = pd.DataFrame(new_rows)
            if out_csv.exists():
                prior = pd.read_csv(out_csv)
                pd.concat([prior, inc], ignore_index=True).to_csv(out_csv, index=False)
            else:
                inc.to_csv(out_csv, index=False)
            new_rows = []

    if new_rows:
        inc = pd.DataFrame(new_rows)
        if out_csv.exists():
            prior = pd.read_csv(out_csv)
            pd.concat([prior, inc], ignore_index=True).to_csv(out_csv, index=False)
        else:
            inc.to_csv(out_csv, index=False)

    final = pd.read_csv(out_csv)
    print(f"\nfinal: {len(final)} rows -> {out_csv}")


if __name__ == "__main__":
    main()
