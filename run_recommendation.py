"""Operationally group core-metric Pettitt points with a grain-step tolerance.

This is a transparent *decision-rule implementation*, not a substitute for
reviewing the actual MK intersections or landscape morphology. MESH is excluded
from the baseline six-core-metric vote, but remains in the statistical outputs.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
import numpy as np
import pandas as pd
from grain_statistics import CORE_METRICS


def choose_grain(summary, retention_limit, step, agreement=4, tolerance_steps=1, alpha=0.05):
    """Choose most-supported observed core breakpoint within retention domain.

    A metric is counted for a candidate if its Pettitt p<alpha and its point
    differs by <= tolerance_steps*step. Tie-break: max exact support; smallest
    total distance; smallest grain. No extrapolated/unobserved grain is created.
    """
    if step <= 0 or agreement < 1 or agreement > 6 or retention_limit <= 0:
        raise ValueError("Invalid step, agreement, or limit")
    sub = summary[summary["metric"].isin(CORE_METRICS)].copy()
    if sub["metric"].duplicated().any():
        raise ValueError("One Pettitt row per core metric expected")
    sub = sub[(sub["pettitt_p_approx"] < alpha) & (sub["pettitt_grain_m"] <= retention_limit)]
    if sub.empty:
        return None, pd.DataFrame()
    candidates = sorted(set(float(v) for v in sub["pettitt_grain_m"]))
    rows = []
    for cand in candidates:
        distance = abs(sub["pettitt_grain_m"].to_numpy(dtype=float) - cand)
        approximate = int(sum(distance <= tolerance_steps * step + 1e-8))
        exact = int(sum(distance < 1e-8))
        rows.append({"candidate_grain_m": cand, "support_n": approximate,
                     "exact_support_n":exact,"total_distance_m":float(sum(distance))})
    ranking = pd.DataFrame(rows).sort_values(
        ["support_n", "exact_support_n", "total_distance_m", "candidate_grain_m"],
        ascending=[False,False,True,True]).reset_index(drop=True)
    if int(ranking.iloc[0]["support_n"]) < agreement:
        return None, ranking
    return float(ranking.iloc[0]["candidate_grain_m"]), ranking


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("summary", help="statistical_summary.csv from run_statistics.py")
    ap.add_argument("--area",required=True)
    ap.add_argument("--retention-limit",type=float,required=True)
    ap.add_argument("--step",type=float,required=True,help="Fine breakpoint-series interval: 5 municipal, 2 district, 1 town")
    ap.add_argument("--agreement",type=int,default=4)
    ap.add_argument("--tolerance-steps",type=int,default=1)
    args = ap.parse_args()
    s = pd.read_csv(args.summary)
    s = s.loc[s["study_area"].astype(str)==args.area]
    chosen, ranking = choose_grain(s,args.retention_limit,args.step,args.agreement,args.tolerance_steps)
    print("Operational candidate (m):",chosen)
    print(ranking.to_string(index=False))
    print("Check MK candidate intervals and corridor/area evidence before treating this as a final recommendation.")

if __name__=="__main__":
    main()
