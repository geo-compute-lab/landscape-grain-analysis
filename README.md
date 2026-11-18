# Supplementary Code S1
## Reproducible analytical workflow for multi-scale landscape grain-size determination

**Associated manuscript:** *Assessing the Effects of Spatial Grain Size on Multi-Scale Coastal Landscape Monitoring: Evidence from Haikou, China*

**Package scope:** This repository provides documented analytical scripts and workflow templates designed to implement the methods described in the manuscript. It does not include example datasets, the restricted Haikou source data, or the actual landscape metric sequences generated for individual grain sizes.

Importantly, the code has not been validated against the restricted 2024 Haikou survey data or the original water-vector source data. Therefore, this repository should be regarded as a methodological implementation resource rather than a complete or exact archive of the scripts used to generate the results reported in the manuscript.

## 1. Included components

| File | Role |
|---|---|
| `grain_statistics.py` | Corrected cumulative sequential MK UF/UB; rank-based Pettitt (approximate p); original and Hamed–Rao modified MK using `pymannkendall` |
| `run_statistics.py` | Read per-grain-size metric sequences from a user-provided CSV/Excel file (including named worksheet/LID selection), run statistical analyses, and export structured results |
| `landscape_methods.py` | Class-level area errors Ei, regional index V, operational screening, and illustrative reference-path water connectivity |
| `run_retention.py` | Determine the earliest grain size triggering an information-loss criterion from user-prepared class-area/corridor tables |
| `run_recommendation.py` | Transparent candidate clustering using six core-metric Pettitt points, a majority threshold, and one-grain-interval tolerance |
| `arcgis10_2_rasterization.py` | **ArcGIS Desktop 10.2 template** for rasterization; requires ArcGIS/arcpy and project-specific configuration |
| `ARCGIS_METHOD_PSEUDOCODE.md` | Data preparation, RMA/RCC, corridor evaluation, and metric-export workflow where proprietary tools are required |
| `tests/test_core.py` | Unit checks for independent numerical and tabular operations |
| `METHODS_AUDIT.md` | Implementation provenance, limitations, and validation status |
| `USER_GUIDE_CN.md` | Chinese usage notes |
| `SUBMISSION_NOTE.md` | Suggested supplementary-code and data-availability wording |

No example or demonstration datasets are distributed with this package. All input files must be prepared independently by the user. The test suite uses test fixtures created within the tests; it does not require a distributed example-data folder.

## 2. Confidentiality and reproduction scope

The source land-use survey data and continuous water-vector data are restricted and are **not included**. The actual per-grain-size landscape metric sequences are also not included because they have not been cleared for public release. No real project file paths, surveyed coordinates, confidential vector features, or empirical input tables are embedded in this package.

Researchers can use the scripts to implement the **method on independently obtained and appropriately prepared input data**. The package alone cannot reproduce the paper's exact empirical 150/50/25-m recommendations or other study-specific numerical results without the original observations and corresponding GIS processing inputs. Do not present outputs generated from unrelated data as validation of the study's reported results.

## 3. Software requirements

For the analytical scripts: Python 3.9 or later, NumPy, pandas, SciPy, `pymannkendall`, and `openpyxl`. Install the dependencies in an isolated environment:

```bash
python -m pip install -r requirements.txt
```

`pymannkendall.original_test` and `pymannkendall.hamed_rao_modification_test` are used for trend tests. Their outputs and numerical p-values should be checked against the package versions and settings used in the study before submission. The **optional ArcPy rasterization script** must run separately in the ArcGIS Desktop 10.2 Python environment (normally Python 2.7), with a valid ArcGIS license. It is **not** compatible with the same Python environment as these modern statistical scripts.

## 4. Input data: statistical analysis

Provide a CSV or Excel workbook with one row per grain size and study area, sorted automatically by `SIZE`. Supported columns:

`LID, SIZE, NP, PD, ENN_MN, PLADJ, COHESION, MESH, AI`

- `SIZE` is a positive grain size in metres; it must be unique for each `LID`.
- `LID` is the study-area identifier; it is optional when the input contains only one region.
- Earlier spreadsheet aliases **`ENNN` -> `ENN_MN`** and **`ESH` -> `MESH`** are handled automatically.
- Metric values must be numeric and finite. Seven landscape metrics are accepted; six (all except MESH) are core inputs to the baseline decision.
- The manuscript's fine-grain sequences are **5–300 m at 5-m steps** (municipal), **2–100 m at 2-m steps** (district), and **1–50 m at 1-m steps** (town). Use the corresponding actual sequences for the relevant study scale.

Run the script with your own prepared input file:

```bash
python run_statistics.py "path/to/your_metrics.csv" --output-dir "path/to/stat_results"
```

For an Excel workbook with a named worksheet and a specific study-area identifier:

```bash
python run_statistics.py "path/to/your_metrics.xlsx" --sheet HAIKOU --area HAIKOU --output-dir "path/to/stat_results"
```

Outputs are `statistical_summary.csv` and `uf_ub_sequences.csv` in the selected output directory. These outputs contain derivatives of the dataset supplied by the user. **Do not upload results derived from restricted data without authorization.** If `pymannkendall` is unavailable, `--skip-trend` can be used only as a limited data-loading/processing smoke test; original and Hamed–Rao MK results will be marked `NOT_RUN`, so this mode is not suitable for scientific reporting:

```bash
python run_statistics.py "path/to/your_metrics.csv" --skip-trend --output-dir "path/to/smoke_test_output"
```

## 5. Input data: information-retention assessment

Provide a user-prepared CSV with one row per **landscape class per grain size**, containing:

`SIZE,class,reference_area,raster_area,corridor_discontinuous`

- `reference_area`: vector-derived area for that class (constant across grain sizes and positive).
- `raster_area`: pixel-count multiplied by cell area for that class, in the same area units.
- `corridor_discontinuous`: a Boolean outcome obtained from the fixed reference-river-path criterion; repeat the same true/false value per `SIZE` across landscape-class rows.
- All grain sizes must have the same set of classes. Keep map boundary/extents and treatment of partial edge cells consistent with the manuscript.

Run:

```bash
python run_retention.py "path/to/your_area_corridor.csv" --output "path/to/retention_summary.csv"
```

The four **operational** failure criteria are: any `|Ei| >= 20%`, any `Ei <= -90%`, regional `V >= 10%`, or representative corridor discontinuity. The output reports the **first grain size meeting any failure criterion**, following the manuscript's *boundary-threshold* convention. This is not automatically the last error-free grain size. Actual information-retention **test step intervals** are 20 m (municipal), 10 m (district), and 5 m (town). These differ from the fine-grain breakpoint-analysis steps.

The `corridor_is_continuous` helper in `landscape_methods.py` demonstrates an **illustrative** Boolean water-path test along a supplied reference corridor mask. It does not derive the river-path mask from GIS source vectors or guarantee exact equivalence to the paper's spatial review. The river-route choice, 4- vs 8-neighbor connectivity, mask buffering, bridge corrections, and edge handling must be documented and verified before computed flags are treated as empirical evidence.

## 6. Recommended grain-size candidate

After running `run_statistics.py` on your own data, pass the resulting `statistical_summary.csv` to the recommendation script. For example:

```bash
python run_recommendation.py "path/to/stat_results/statistical_summary.csv" --area HAIKOU --retention-limit 90 --step 5 --agreement 4 --tolerance-steps 1
```

Replace the area identifier, retention limit, and fine-sequence interval with values appropriate to the input data and study scale. This decision routine uses six core metrics `NP, PD, ENN_MN, PLADJ, COHESION, AI`, statistically supported Pettitt points (p < 0.05), an inclusive grain-size retention boundary, agreement by at least four of six metrics by default, and one *fine-sequence* interval of positional tolerance; **MESH remains supplementary**. It reports a candidate, not a certified final recommendation. Researchers must inspect the sequential MK candidate ranges, area/corridor evidence, and ambiguous clusters. The study also examined 50/60/75% and reduced-metric alternatives; applicable sensitivity checks must be run and recorded rather than assumed from the default.

## 7. ArcGIS Desktop 10.2 rasterization and shifts

Open `arcgis10_2_rasterization.py` in the **ArcGIS 10.2 Python environment**, configure the input polygon file, integer `CLASS_ID`, projected coordinates and fixed extent, output directories, and separate grain-size sequences. The template builds shifted alignment rasters and calls ArcPy `PolygonToRaster_conversion` with:

- `MAXIMUM_AREA` for RMA (maximum-area rule)
- `CELL_CENTER` for RCC (cell-center rule)

The origin offsets are `original`, `X + 0.25g`, `Y + 0.25g`, and `XY + 0.5g`; `g` is the **current** cell size, not a fixed distance. The template **has not been executed** here because ArcPy and the restricted geometry are unavailable. It also does not compute landscape metrics; these must be exported with the same FRAGSTATS or equivalent landscape-index definitions/settings used in the study. See `ARCGIS_METHOD_PSEUDOCODE.md`.

## 8. Validation and methodological cautions

The numerical utilities, input validation, class-area screening, corridor Boolean helper, and candidate grouping have unit tests in `tests/test_core.py`. Run the tests with:

```bash
python -m pytest tests -q
```

End-to-end MK/Hamed–Rao tests were **not run** in the authoring environment (the required package was not installed), and the ArcGIS template was **not executed** (ArcGIS was unavailable). The original empirical sequences were not supplied, so neither original nor modified code has been checked for exact agreement with published 150/50/25-m values.

Pettitt's p-values are asymptotic approximations; ranked metrics at adjacent grain sizes are serially dependent, so significance should not be overinterpreted. UF–UB crossing positions are **descriptive candidate ranges** and not independently significant breakpoint tests. In case of discrepancies, use the manuscript's explicitly reported definitions, verified study software/parameters, and original metric series; do not force software to reproduce a preferred number.

## 9. Reproducibility and data preparation

This package does not provide sample input files. Before running the scripts, prepare the statistical metric table and/or information-retention table in the formats specified in Sections 4 and 5. Keep restricted source data and generated outputs in an authorized local environment. Verify all input fields, units, study-area identifiers, grain-size sequences, GIS processing parameters, and software versions before interpreting or reporting results.

Documentation and code should be checked against the actual research workflow before submission as Supplementary Code S1.
