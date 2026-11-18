# Code provenance, corrections, and validation

The analytical methods and workflows represented in this package were applied to the Haikou study data during the research reported in the manuscript. This repository organizes the scripts and workflow documentation for review and reference. Python fragments were found primarily on PDF pages **14–16, 19–24, 28, 33–38, 43–47, and 54–56**. These focus on reading LID/SIZE tables, original MK trend tests, sequential UF/UB calculations, rank-based Pettitt tests, and output formatting. They do not establish an intact original ArcGIS rasterization script or an independent landscape-metric calculation engine.

| Method | In historical PDF? | Treatment in this package |
|---|---|---|
| Excel/CSV inputs, optional LID and worksheet | Yes | Rewritten with validation, automatic grain sorting, and alias handling |
| Original MK trend | Yes (`pymannkendall.original_test`) | Retained as dependency |
| Sequential MK UF/UB | Yes, but inconsistent early implementations | Corrected **cumulative** pair count, correct sample-count indexing and tie handling, reversed sign for UB; crossing is descriptive |
| Pettitt | Yes, rank-based function | Preserved rank formulation, excluded empty final split, capped approximate p at 1, explicit grain-at-index convention |
| Hamed–Rao modified MK | Named later in paper, not implemented in early PDF snippets | Added `pymannkendall.hamed_rao_modification_test` |
| Ei / V | Equations discussed in early PDF and revised manuscript | Added numerical functions and independent tests for RMS percent-error V |
| Retention limit | Verbal decision rule in PDF/manuscript | Added earliest-trigger logic; baseline threshold |Ei| 20%, V 10%, loss 90%, binary corridor condition |
| Corridor path continuity | Qualitative in PDF/manuscript | Added **illustrative** constrained water-path helper; actual GIS reference mask/route needs project validation |
| RMA/RCC rasterization and origin shifts | Rules described, but no complete runnable ArcGIS code found | Added **ArcGIS 10.2 template** and platform-independent pseudocode, no proprietary source files |
| Multi-metric recommendation | Described in revised manuscript | Added transparent operational decision-candidate routine (six core metrics; MESH supplementary) |
| Calculation of seven FRAGSTATS-equivalent metrics | Not present as complete code | **Not invented**; remains an external landscape-metric stage requiring exact verified parameter settings |

## Key historical computation correction

The old MK code in the PDF originally counted only comparisons for the current observation, rather than the **cumulative** increasing-pairs count, and used an inconsistent variance term at a zero-based index. The final historical snippet became cumulative but still used `2*k+5` where `2*k+7` is required under its zero-based convention for non-tied data. This implementation uses the number of observations `m=k+1` directly:

- `E(S_m)=[m(m−1)−sum_j t_j(t_j−1)]/4`.
- `Var(S_m)=[m(m−1)(2m+5)−sum_j t_j(t_j−1)(2t_j+5)]/72`.

Any new UF/UB intersections **may differ** from historic outputs; recalculate with the actual metric sequences and document any differences instead of treating the PDF's early outputs as ground truth. The standard Pettitt location here is assigned to the index of `argmax |U_t|`, the split **after** that observation; a different convention could move a reported location by one grain step. Neither alone gives an alignment-independent ecological threshold.

## Verification conducted

- **Passed:** seven automated tests using test fixtures created within the test suite, covering the original test suite scope. The test file is provided at the repository root as `test_core.py`.
- **Smoke tested:** CSV statistical output using `--skip-trend`; this does **not** calculate the actual original/Hamed–Rao MK statistics.
- **Not run in this packaging environment:** end-to-end original and Hamed–Rao MK execution, because `pymannkendall` was not installed here. This packaging-environment limitation is distinct from the fact that the analytical methods and workflows represented in the package were applied to the Haikou study data during the research.
- **Not run here:** ArcGIS 10.2 and proprietary geometry operations (ArcPy environment absent).
- **Study application:** The methods and workflows in this package were applied to the Haikou study data.
- **Data availability:** The original Haikou data and per-grain-size metric sequences are not included in the public repository, so the exact study results cannot be reproduced from this package alone.

Before submission, the author should verify the environment, genuine metric series, 4/8-neighbor path convention, actual rasterization settings, code outputs and consistency with the paper's Methods and Table S1. Present this as supplementary code documenting the methods and workflows applied in the Haikou study.
