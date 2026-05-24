from dl import queryClient as qc
import pandas as pd
from io import StringIO

coords = [
    ("2003ic", 10.4593, -9.3053),
    ("2943", 17.7049, 1.0079),
    ("2006ef", 31.0813, -8.7284),
    ("1306029", 40.8416, -1.9578),
    ("2009D", 58.5951, -19.1817),
    ("2008hv", 136.8920, 3.3923),
    ("350192", 148.7160, 1.9617),
    ("PS16bnz", 155.1540, -2.4668),
    ("PS17bii", 171.4090, 7.3336),
    ("SN2017hn", 196.9140, 6.3376),
    ("2007ca", 202.7740, -15.1018),
    ("PTSS17-niq", 215.0690, 15.3417),
    ("AT2016ews", 225.6520, 23.3528),
    ("2002de", 244.1270, 35.7084),
    ("2013bs", 259.3420, 41.0667),
    ("160197", 241.6170, 53.8718),
]

rows = []

for cid, ra, dec in coords:
    sql = f"""
    SELECT COUNT(*) AS n
    FROM ls_dr9.tractor
    WHERE q3c_radial_query(ra, dec, {ra}, {dec}, 1.0)
      AND flux_r > 0
      AND flux_z > 0
    """
    out = qc.query(sql=sql, fmt="csv")
    n = int(pd.read_csv(StringIO(out))["n"].iloc[0])
    rows.append({"CID": cid, "RA": ra, "DEC": dec, "count_1deg": n})
    print(cid, n)

pd.DataFrame(rows).to_csv("pantheon_next_counts.csv", index=False)
