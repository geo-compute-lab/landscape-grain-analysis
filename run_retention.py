"""Compute the first operational information-loss threshold from an area-and-corridor CSV.

Expected fields: SIZE,class,reference_area,raster_area,corridor_discontinuous.
Each SIZE must have exactly the same landscape classes; corridor value repeats by class.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from landscape_methods import area_errors, retention_screen


def parse_bool(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if str(v).strip().lower() in ("true", "1", "yes"):
        return True
    if str(v).strip().lower() in ("false", "0", "no"):
        return False
    raise ValueError("Invalid corridor_discontinuous flag: " + str(v))


def evaluate(df):
    req = {"SIZE", "class", "reference_area", "raster_area", "corridor_discontinuous"}
    if req.difference(df.columns):
        raise ValueError("Missing columns: " + ", ".join(sorted(req.difference(df.columns))))
    df = df.copy()
    df["SIZE"] = pd.to_numeric(df["SIZE"], errors="raise")
    if df.groupby("class")["reference_area"].nunique().max() > 1:
        raise ValueError("Reference area for each class must be constant across grains")
    areas = []
    classes = set(df["class"])
    for grain, grp in df.groupby("SIZE", sort=True):
        if set(grp["class"]) != classes or grp["class"].duplicated().any():
            raise ValueError("Every grain must have exactly one record for every class")
        # Preserve class order for reference/raster alignment.
        grp = grp.set_index("class").loc[sorted(classes)]
        reference = grp["reference_area"].astype(float).to_numpy()
        raster = grp["raster_area"].astype(float).to_numpy()
        flags = {parse_bool(x) for x in grp["corridor_discontinuous"]}
        if len(flags) != 1:
            raise ValueError("Inconsistent corridor value at SIZE %s" % grain)
        e = area_errors(reference, raster)
        v, reasons = retention_screen(e, flags.pop())
        areas.append({"SIZE":float(grain),"V_percent":v,"max_abs_Ei_percent":float(max(abs(e))),
                      "min_Ei_percent":float(min(e)),**reasons,"any_criterion":any(reasons.values())})
    result = pd.DataFrame(areas).sort_values("SIZE")
    first = result.loc[result["any_criterion"],"SIZE"]
    return result, (float(first.iloc[0]) if not first.empty else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="CSV with one row per landscape class per grain size")
    ap.add_argument("--output", default="retention_summary.csv")
    a = ap.parse_args()
    result, first = evaluate(pd.read_csv(a.input))
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(a.output,index=False)
    print("First criterion-exceedance grain (operational retention limit):", first)
    print(result.to_string(index=False))

if __name__ == "__main__":
    main()
