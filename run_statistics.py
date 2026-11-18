"""Run MK + Hamed--Rao + sequential UF/UB + Pettitt on CSV/Excel metric sequences.

Example (synthetic data):
    python run_statistics.py path/to/your_metrics.csv --output-dir path/to/output
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from grain_statistics import ALL_METRICS, ALIASES, sequential_mk, uf_ub_candidates, pettitt_test, mk_trends


def load_metrics(path, sheet=None, area=None):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        data = pd.read_csv(path)
    elif path.suffix.lower() in (".xlsx", ".xlsm"):
        data = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    else:
        raise ValueError("Supported inputs: CSV, XLSX, XLSM")
    data.columns = [str(v).strip() for v in data.columns]
    data = data.rename(columns={k: v for k, v in ALIASES.items() if k in data.columns})
    if len(data.columns) != len(set(data.columns)):
        raise ValueError("Column aliases created duplicate names (e.g., ENNN and ENN_MN).")
    if "SIZE" not in data:
        raise ValueError("Missing SIZE column (grain size in meters)")
    if area is not None:
        if "LID" not in data:
            raise ValueError("--area needs a LID column")
        data = data.loc[data["LID"].astype(str).str.strip() == area]
    if data.empty:
        raise ValueError("No records after filtering")
    if "LID" not in data:
        data = data.assign(LID=area or "STUDY_AREA")
    groups = []
    for region, group in data.groupby("LID", sort=True):
        group = group.copy()
        group["SIZE"] = pd.to_numeric(group["SIZE"], errors="raise")
        group = group.sort_values("SIZE")
        if group["SIZE"].duplicated().any():
            raise ValueError("Duplicate SIZE within study area: "+str(region))
        if not np.isfinite(group["SIZE"].to_numpy(dtype=float)).all():
            raise ValueError("Invalid grain sizes")
        groups.append((str(region), group))
    return groups


def analyse(groups, lag=None, skip_trend=False):
    summary_rows, curve_rows = [], []
    for area, data in groups:
        grains = data["SIZE"].to_numpy(dtype=float)
        for metric in ALL_METRICS:
            if metric not in data.columns:
                continue
            values = pd.to_numeric(data[metric], errors="raise").to_numpy(dtype=float)
            if not np.isfinite(values).all():
                raise ValueError("Missing/nonfinite values in %s / %s" % (area, metric))
            uf, ub = sequential_mk(values)
            cross = uf_ub_candidates(grains, uf, ub)
            pet = pettitt_test(values, grains)
            if skip_trend:
                # Smoke-test-only path; do not treat missing trend values as completed MK tests.
                trend = {"mk_trend": "NOT_RUN", "mk_z": np.nan, "mk_p": np.nan,
                         "mk_tau": np.nan, "hamed_rao_trend": "NOT_RUN",
                         "hamed_rao_z": np.nan, "hamed_rao_p": np.nan,
                         "hamed_rao_lag": "NOT_RUN"}
            else:
                trend = mk_trends(values, lag=lag)
            summary_rows.append({
                "study_area": area, "metric": metric, "role": "supplementary" if metric == "MESH" else "core",
                **trend, "uf_ub_candidates_m": ";".join(str(int(v) if v.is_integer() else v) for v in cross),
                "pettitt_index_0based": pet["index"], "pettitt_grain_m": pet["grain_m"],
                "pettitt_K": pet["K"], "pettitt_p_approx": pet["p_approx"],
            })
            for g, v, a, b in zip(grains, values, uf, ub):
                curve_rows.append({"study_area":area,"metric":metric,"SIZE":g,"value":v,"UF":a,"UB":b})
    if not summary_rows:
        raise ValueError("No valid metric columns: expected " + ", ".join(ALL_METRICS))
    return pd.DataFrame(summary_rows), pd.DataFrame(curve_rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="CSV or Excel file with SIZE and NP/PD/ENN_MN/PLADJ/COHESION/MESH/AI")
    ap.add_argument("--sheet", default=None, help="Worksheet name, e.g. HAIKOU")
    ap.add_argument("--area", default=None, help="Optional LID filter, e.g. HAIKOU")
    ap.add_argument("--lag", type=int, default=None, help="Hamed-Rao number of lags (default: package default)")
    ap.add_argument("--output-dir", default="output", help="Local folder (do not publish outputs from restricted data without approval)")
    ap.add_argument("--skip-trend", action="store_true", help="Smoke-test mode only: OMIT original and Hamed-Rao trend tests")
    args = ap.parse_args()
    groups = load_metrics(args.input, sheet=args.sheet, area=args.area)
    summary, curves = analyse(groups, lag=args.lag, skip_trend=args.skip_trend)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output/"statistical_summary.csv", index=False)
    curves.to_csv(output/"uf_ub_sequences.csv", index=False)
    print(summary[["study_area","metric","hamed_rao_z","hamed_rao_p","uf_ub_candidates_m","pettitt_grain_m","pettitt_K","pettitt_p_approx"]].to_string(index=False))
    if args.skip_trend:
        print("WARNING: --skip-trend omitted the original and Hamed-Rao MK statistics. These are NOT final analysis results.")
    print("Files saved in:", output.resolve())

if __name__ == "__main__":
    main()
