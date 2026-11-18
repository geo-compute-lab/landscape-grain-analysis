"""Area error, V, retention threshold and corridor connectivity helpers.

All functions work on non-restricted tabular/Boolean inputs. Spatial overlays,
landscape metrics and precise reference river masks must be prepared separately.
"""
from __future__ import annotations
import numpy as np
from collections import deque


def area_errors(reference_areas, raster_areas):
    """Ei (%) = 100 * (Ai-A0i)/A0i. All classes must have positive reference area."""
    baseline = np.asarray(reference_areas, dtype=float)
    after = np.asarray(raster_areas, dtype=float)
    if baseline.shape != after.shape or baseline.ndim != 1 or not len(baseline):
        raise ValueError("Reference and raster areas must be equal-length one-dimensional arrays")
    if (baseline <= 0).any() or (after < 0).any() or not np.isfinite(baseline).all() or not np.isfinite(after).all():
        raise ValueError("Reference area must be positive, raster area nonnegative, values finite")
    return (after - baseline) / baseline * 100.0


def regional_V(error_percent):
    """V (%) = sqrt(mean(Ei^2)) based on percentage-class area errors."""
    e = np.asarray(error_percent, dtype=float)
    if e.ndim != 1 or len(e) == 0 or not np.isfinite(e).all():
        raise ValueError("Provide a one-dimensional finite list of percent errors")
    return float(np.sqrt(np.mean(np.square(e))))


def retention_screen(error_percent, corridor_discontinuous, class_error_cutoff=20.0,
                     V_cutoff=10.0, near_disappearance_loss=90.0):
    e = np.asarray(error_percent, dtype=float)
    v = regional_V(e)
    failures = {
        "class_area_error": bool(np.any(np.abs(e) >= class_error_cutoff)),
        "regional_V": bool(v >= V_cutoff),
        "near_disappearance": bool(np.any(e <= -near_disappearance_loss)),
        "corridor_discontinuous": bool(corridor_discontinuous),
    }
    return v, failures


def corridor_is_continuous(water_mask, reference_corridor_mask, start, end, connectivity=4):
    """Boolean corridor continuity between two fixed route endpoints.

    Water-path search is restricted to the provided *reference corridor mask*.
    This illustrates a reproducible binary check, NOT a validated replacement
    for the paper's manually verified original river-path method. The mask,
    endpoint matching, and 4/8-neighbor setting must be fixed *before* tests.
    """
    water = np.asarray(water_mask, dtype=bool)
    path = np.asarray(reference_corridor_mask, dtype=bool)
    if water.ndim != 2 or path.shape != water.shape:
        raise ValueError("water_mask and reference_corridor_mask must have the same 2D shape")
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    h, w = water.shape
    for r,c in (start,end):
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError("start or end outside grid")
    valid = water & path
    if not valid[start] or not valid[end]:
        return False
    steps = ((1,0),(-1,0),(0,1),(0,-1))
    if connectivity == 8:
        steps += ((1,1),(1,-1),(-1,1),(-1,-1))
    seen = {tuple(start)}
    q = deque([tuple(start)])
    while q:
        r,c = q.popleft()
        if (r,c) == tuple(end):
            return True
        for dr,dc in steps:
            rr,cc = r+dr,c+dc
            if 0 <= rr < h and 0 <= cc < w and valid[rr,cc] and (rr,cc) not in seen:
                seen.add((rr,cc))
                q.append((rr,cc))
    return False
