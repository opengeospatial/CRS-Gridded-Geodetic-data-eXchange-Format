#!/usr/bin/python3

from osgeo import gdal
import yaml
import argparse

help = """
Utility script to compile YAML format GGXF grid headers corresponding to
a GDAL source grid.  Nested grid structures are dumped as GGXF nested grids
(ie using proposed YAML data structure rather than parentGridName attribute)
"""


def main():
    parser = argparse.ArgumentParser(
        "Compile GGXF grid headers from a GDAL supported grid file"
    )
    parser.add_argument("grid_data_file", help="Name of input grid file")
    parser.add_argument(
        "output_grid_headers_file",
        help="Name of file to which YAML grid headers are written",
    )
    args = parser.parse_args()
    grid_file = args.grid_data_file
    yaml_file = args.output_grid_headers_file

    root = gdal.Open(grid_file)
    datasets = [root]
    for fname, name in root.GetSubDatasets():
        subset = gdal.Open(fname)
        datasets.append(subset)
    grids = {}
    parents = {}
    for dataset in datasets:
        description = dataset.GetDescription()
        meta = dataset.GetMetadata_Dict()
        name = meta.get("SUB_NAME", description)
        parent = meta.get("PARENT", "NONE")
        tfm = dataset.GetGeoTransform()
        coeffs = [
            tfm[3] + tfm[5] / 2.0,
            tfm[4],
            tfm[5],
            tfm[0] + tfm[1] / 2,
            tfm[1],
            tfm[2],
        ]
        if name in grids:
            raise RuntimeError(f"Grid name {name} is duplicated")
        grids[name] = {
            "gridName": name,
            "affineCoeffs": coeffs,
            "iNodeCount": dataset.RasterXSize,
            "jNodCount": dataset.RasterYSize,
            "dataSource": description,
        }
        if parent != "NONE":
            parents[name] = parent

    rootgrids = []
    for name, grid in grids.items():
        if name not in parents:
            rootgrids.append(grid)
        else:
            pgrid = grids.get(parents[name])
            if pgrid is None:
                raise RuntimeError(f"Parent grid {parents[name]} not defined")
            if "grids" not in pgrid:
                pgrid["grids"] = []
            pgrid["grids"].append(grid)

    with open(yaml_file, "w") as outh:
        for g in rootgrids:
            printGrid(g, outh)


def printGrid(g, outh, indent="  - "):
    for key, val in g.items():
        if key != "grids":
            print(f"{indent}{key}: {val}", file=outh)
        else:
            print(f"{indent}grids:", file=outh)
            for grid in val:
                printGrid(grid, outh, indent + "  - ")
        indent = indent.replace("-", " ")


if __name__ == "__main__":
    main()
