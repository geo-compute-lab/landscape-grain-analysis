# Supplementary Code S1 — ArcGIS rasterization and landscape-metric workflow

The following is a transparent reconstruction of the **stated method**, rather than a claim that the full original spatial workflow scripts were preserved in the historical PDF. The runnable `arcgis10_2_rasterization.py` file is an environment-specific template requiring independent GIS data and ArcGIS Desktop 10.2.

## A. Data preparation (no source data distributed)

1. Obtain authorized land-use polygon and continuous-water vector datasets independently.
2. Standardize coordinate reference system, land-cover categories and geometry validity. Integrate bridge/road-crossing river segments according to the original water-processing protocol.
3. Clip each study unit using a **fixed** analysis boundary and use a projected coordinate system (metres) throughout.
4. Encode eight land-use classes as numerical values and preserve the code-to-name lookup privately.
5. Retain original vector area by class to calculate Ei; the 1-m reference raster is for *morphological visualization only*, not the official area baseline.

## B. RMA/RCC and shifted origins

```
for study_unit in [municipal, district, town]:
    hold study-unit extent and class definitions fixed
    retention_grains = sequence(start, stop, interval=20/10/5 metres)
    fine_breakpoint_grains = sequence(5..300 / 2..100 / 1..50, interval=5/2/1 metres)
    for grain g in union(retention_grains, fine_breakpoint_grains):
        for origin (dx,dy) in [(0,0),(.25*g,0),(0,.25*g),(.5*g,.5*g)]:
            set fixed analysis boundary/coordinate system and a snap raster
            whose origin is shifted by (dx,dy)
            RMA = PolygonToRaster(input, class_field, MAXIMUM_AREA, cellsize=g)
            RCC = PolygonToRaster(input, class_field, CELL_CENTER, cellsize=g)
            record exact raster origin, extent, pixel size, NoData and spatial reference
```

**Important:** For the main published workflow, the rasterization rule **RMA** was selected for subsequent spatial pattern indices. Both RMA and RCC were used in the initial rule comparison/information-retention assessment. For any sensitivity rerun, apply the **same original rule-selection and screening procedure**, documenting exactly which rule supports each threshold. Do not silently interchange a threshold under RCC with one under RMA.

## C. Regional information retention

For each coarser grid:

- Compute rasterized landscape area per class from classified pixel counts and pixel area, using a consistently specified edge/NoData policy.
- Compute class-level percentage error `Ei = 100 * (Ai - A0i) / A0i` relative to the **original vector area** `A0i`.
- Compute regional `V = sqrt(mean(Ei^2))` across the study's classes, in percent units.
- Compare the focal river path with raster water cells; flag discontinuity if one or more non-water-cell interruptions sever its connected representation. River path, endpoints, permitted corridor buffer, and connectivity convention must be kept constant.
- The *earliest sampled grain* that triggers any of the following is the study's operational information-retention boundary: `abs(Ei)>=20%`, `Ei<=-90%`, `V>=10%`, or binary river-corridor discontinuity.
- For sensitivity to operational criteria, vary class-error thresholds `20/25/30%`, V thresholds `10/12.5/15%`, and loss thresholds `80/90/95%` where applicable; do not confuse this analysis with raster-origin sensitivity.

## D. Landscape pattern metrics

For each fine grain size, calculate (using the same 4-neighbor / eight-class and aggregation conventions as the verified study implementation, wherever applicable):

- NP, PD, ENN_MN, PLADJ, COHESION, MESH and AI.
- `ENN_MN` and `MESH` may appear as `ENNN` and `ESH` in early Excel sheets; map aliases carefully.
- Export `LID, SIZE, NP, PD, ENN_MN, PLADJ, COHESION, MESH, AI` to a local CSV/Excel table.

**Not automated here:** The historical source does **not** contain a complete, verifiable landscape metric calculation program (FRAGSTATS or an exact equivalent). Computing these metrics afresh requires verified definitions of landscape-level aggregation, handling of background and boundaries, cell adjacency, nearest-neighbor eligibility, and landscape extent. The statistical package therefore consumes already-computed metric sequences rather than inventing a metric engine with potentially different definitions.

## E. Change-point and recommendation procedures

1. Sort each metric's grain-size sequence by `SIZE`; never treat Excel row order as analytical order.
2. Compute original MK trend and Hamed–Rao modified MK (serial correlation robustness). Record each Z and p.
3. Compute cumulative sequential MK UF/UB candidate intersections. They are **not** Pettitt statistics and are not automatic significance declarations.
4. Compute Pettitt rank statistic K and approximate p; map the maximizing index to its sampled grain size using the declared split convention.
5. Group the six core metrics' statistically supported Pettitt breakpoints, separately report MESH supplementary outcomes, and identify a dominant cluster at or within the operational retention boundary. Default: four of six; examine one-fine-grain tolerance and 50%/60%/75% agreement alternatives.
6. Independently inspect every reported threshold and the river continuity evidence. Do not change rounding, index mapping, or tolerance post hoc to force agreement with a previously published result.

## F. Disclosures / limitations

The code can implement the method on *independent* permissible data. It cannot reproduce Haikou's exact numerical tables without the restricted raster/vector inputs or real per-grain metric series. The ArcGIS template and the specific continuity implementation must be validated on the project GIS setup before representing them as the actual software used in the experiment.
