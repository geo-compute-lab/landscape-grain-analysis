"""Statistical helpers for grain-size sequences (independent of restricted GIS data).

Note: sequential UF/UB is a diagnostic, not a significance test for a breakpoint.
Pettitt's p-value is the standard large-sample approximation.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.stats import rankdata

CORE_METRICS = ("NP", "PD", "ENN_MN", "PLADJ", "COHESION", "AI")
ALL_METRICS = ("NP", "PD", "ENN_MN", "PLADJ", "COHESION", "MESH", "AI")
ALIASES = {"ENNN": "ENN_MN", "ESH": "MESH"}


def validate_series(values):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 4 or not np.isfinite(x).all():
        raise ValueError("A metric sequence must contain at least four finite numeric values.")
    return x


def progressive_uf(values):
    """Cumulative sequential MK UF using pair-increase counts, with tie adjustment.

    At position k (zero based), m=k+1 observations have been seen:
    E(S_m) = [m(m-1) - sum_t t(t-1)]/4 (ties excluded);
    Var(S_m) = [m(m-1)(2m+5) - sum_t t(t-1)(2t+5)]/72.
    This is a *cumulative* statistic. Older non-cumulative scripts do not implement it.
    """
    x = validate_series(values)
    n = x.size
    uf = np.zeros(n, dtype=float)
    pair_count = 0.0
    for k in range(1, n):
        pair_count += float(np.count_nonzero(x[k] > x[:k]))
        m = k + 1
        _, counts = np.unique(x[:m], return_counts=True)
        tie_term = float(np.sum(counts * (counts - 1) * (2 * counts + 5)))
        variance = (m * (m - 1) * (2 * m + 5) - tie_term) / 72.0
        expected = (m * (m - 1) - float(np.sum(counts * (counts - 1)))) / 4.0
        uf[k] = (pair_count - expected) / math.sqrt(variance) if variance > 0 else 0.0
    return uf


def sequential_mk(values):
    """UF and reverse-oriented UB curves. No p-value attached to crossings."""
    x = validate_series(values)
    return progressive_uf(x), -progressive_uf(x[::-1])[::-1]


def uf_ub_candidates(grains, uf, ub):
    """Grid locations bracketing *internal* UF/UB sign changes; descriptive only.

    Excludes the trivial first/last initialization at zero, and does not interpolate
    a precise physical breakpoint from the discrete grain-size sequence.
    """
    g = np.asarray(grains, dtype=float)
    d = np.asarray(uf, float) - np.asarray(ub, float)
    if len(g) != len(d):
        raise ValueError("grains and UF/UB must have matching lengths")
    candidates = []
    # Use strict sign reversals to avoid zero initialization artifacts.
    for i in range(1, len(g)-2):
        if d[i] * d[i+1] < 0:
            candidates.append(float(g[i+1]))
    return candidates


def pettitt_test(values, grains):
    """Pettitt rank-based change point; convention: grain at argmax |U_t|.

    A break at index t is the split AFTER t; p is an approximation and does
    not correct for serial dependence in the ordered grain-size observations.
    """
    x = validate_series(values)
    g = np.asarray(grains, dtype=float)
    if len(g) != len(x) or np.any(np.diff(g) <= 0):
        raise ValueError("grains must be strictly ascending and match values")
    n = len(x)
    ranks = rankdata(x, method="average")
    kseq = 2 * np.cumsum(ranks) - np.arange(1, n+1) * (n+1)
    # The final split is empty; exclude that position.
    t = int(np.argmax(np.abs(kseq[:-1])))
    K = float(abs(kseq[t]))
    p = float(min(1.0, 2 * math.exp(-6 * K * K / (n**3 + n**2))))
    return {"index": t, "grain_m": float(g[t]), "K": K, "p_approx": p}


def mk_trends(values, lag=None):
    """Original and Hamed--Rao modified MK using the published pymannkendall API.

    `lag=None` uses all statistically significant lags as in the package default.
    Raises an informative error if pymannkendall is not installed.
    """
    x = validate_series(values)
    try:
        import pymannkendall as mk
    except ImportError as e:
        raise RuntimeError("Install pymannkendall (pip install -r requirements.txt) "+
                           "to calculate original/Hamed--Rao MK tests") from e
    standard = mk.original_test(x)
    modified = mk.hamed_rao_modification_test(x, lag=lag)
    return {
        "mk_trend": standard.trend,
        "mk_z": float(standard.z),
        "mk_p": float(standard.p),
        "mk_tau": float(standard.Tau),
        "hamed_rao_trend": modified.trend,
        "hamed_rao_z": float(modified.z),
        "hamed_rao_p": float(modified.p),
        "hamed_rao_lag": "all significant" if lag is None else str(lag),
    }
