# -*- coding: utf-8 -*-
"""ArcGIS Desktop 10.2 / ArcPy *template* for RMA/RCC and shifted grid origins.

Requires ArcGIS Desktop 10.2 (Python 2.7) and independently licensed polygon
features. NOT runnable/tested in the present environment without ArcPy.
Edit all configuration paths, integer land-class field, extent, and spatial
reference before running. A spatially aligned 1x1 'snap' raster is built from
an ESRI ASCII raster for each requested origin and grain size.
"""
from __future__ import print_function
import os
import arcpy

# ---------------- USER CONFIGURATION (REPLACE, NO REAL DATA BUNDLED) -----------
INPUT_POLYGONS = r"C:\YOUR_PROJECT\input\land_classes.shp"
CLASS_FIELD = "CLASS_ID"  # integer codes 1..8, one polygon/class
OUTPUT_FOLDER = r"C:\YOUR_PROJECT\output"
WORKSPACE = r"C:\YOUR_PROJECT\scratch"
# Fixed analysis extent and reference origin in a projected coordinate system (metres)
XMIN, YMIN, XMAX, YMAX = 0.0, 0.0, 10000.0, 10000.0
GRAIN_SIZES_M = [20, 40, 60]  # EXAMPLE ONLY; replace with study's configured series
OFFSET_CONFIGS = {"original": (0.0,0.0), "x025": (0.25,0.0),
                  "y025": (0.0,0.25), "xy050":(0.5,0.5)}
RASTER_RULES = {"RMA":"MAXIMUM_AREA", "RCC":"CELL_CENTER"}
# ------------------------------------------------------------------------------


def build_snap_ascii(filename, x, y, grain):
    """Create a tiny georeferenced raster anchoring the target cell lattice.

    ASCII raster stores its lower-left origin in map coordinates. ArcPy converts
    it to raster; DefineProjection attaches the input polygon spatial reference.
    """
    with open(filename, "w") as f:
        f.write("ncols 1\n")
        f.write("nrows 1\n")
        f.write("xllcorner %.9f\n" % x)
        f.write("yllcorner %.9f\n" % y)
        f.write("cellsize %.9f\n" % grain)
        f.write("NODATA_value -9999\n")
        f.write("1\n")


def main():
    if not arcpy.Exists(INPUT_POLYGONS):
        raise IOError("Please configure INPUT_POLYGONS before running")
    for folder in (OUTPUT_FOLDER,WORKSPACE):
        if not os.path.isdir(folder):
            os.makedirs(folder)
    sr = arcpy.Describe(INPUT_POLYGONS).spatialReference
    if sr.type != "Projected":
        raise ValueError("Use a projected coordinate system with metre units")
    arcpy.env.overwriteOutput = True
    arcpy.env.outputCoordinateSystem = sr
    arcpy.env.extent = arcpy.Extent(XMIN, YMIN, XMAX, YMAX)
    for grain in GRAIN_SIZES_M:
        for label,(fx,fy) in OFFSET_CONFIGS.items():
            # Origin shift is proportional to the current cell size (g).
            x = XMIN + grain * fx
            y = YMIN + grain * fy
            tag = "%s_%sm" % (label,int(grain))
            asc = os.path.join(WORKSPACE, "snap_"+tag+".asc")
            snap = os.path.join(WORKSPACE, "snap_"+tag+".tif")
            build_snap_ascii(asc,x,y,grain)
            arcpy.ASCIIToRaster_conversion(asc,snap,"INTEGER")
            arcpy.DefineProjection_management(snap,sr)
            arcpy.env.snapRaster = snap
            arcpy.env.cellSize = grain
            for rule,assignment in RASTER_RULES.items():
                dest = os.path.join(OUTPUT_FOLDER,"%s_%s.tif" % (rule,tag))
                arcpy.PolygonToRaster_conversion(INPUT_POLYGONS, CLASS_FIELD,
                      dest, assignment,"NONE",grain)
                print("Created:",dest)
    arcpy.env.snapRaster = None
    print("Next: compute area tables and river-corridor flags from these rasters.")

if __name__ == "__main__":
    main()
