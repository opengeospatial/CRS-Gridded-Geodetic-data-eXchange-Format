#!/usr/bin/python3

from osgeo import gdal
import yaml
import json
import argparse
import re

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
    parser.add_argument(
        "-p",
        "--parameters",
        help="'/' delimited list of parameter names, optionally followed by :##.## scale factor",
    )
    args = parser.parse_args()
    grid_file = args.grid_data_file
    yaml_file = args.output_grid_headers_file

    root = gdal.Open(grid_file)
    datasets = [root]
    parameters = []
    for band in range(root.RasterCount):
        rb = root.GetRasterBand(band + 1)
        name = rb.GetDescription()
        name = name.strip()
        name = re.sub(r"[^\w\s].*", "", name)
        name = re.sub(r"\s+(\w)", lambda m: m.group(1).upper(), name.lower())
        name = re.sub(r"\s+", "", name)
        if name == "":
            name = f"band{band}"
        parameters.append(name)

    transform = None
    if args.parameters:
        argparams = args.parameters.split("/")
        if len(argparams) != len(parameters):
            raise RuntimeError(
                f"Parameters argument {args.parameters} must have {len(parameters)} / delimited values"
            )
        parameters = []
        for param in argparams:
            if ":" in param:
                (param, scale) = param.rsplit(":", maxsplit=1)
                scale = float(scale)
                transform = transform or []
                transform.append({"parameterName": param, "scale": scale})
            parameters.append(param)

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
        datasource = {"sourceType": "GDAL", "gdalSource": description}
        if transform:
            datasource["parameterTransformation"] = transform
        grids[name] = {
            "gridName": name,
            # Some shenanigans to bring coefficients onto one line
            "affineCoeffs": json.dumps(coeffs),
            "iNodeCount": dataset.RasterXSize,
            "jNodeCount": dataset.RasterYSize,
            "dataSource": datasource,
        }
        if parent != "NONE":
            parents[name] = parent

    # Compile nested grid structure
    rootgrids = []
    for name, grid in grids.items():
        if name not in parents:
            rootgrids.append(grid)
        else:
            pgrid = grids.get(parents[name])
            if pgrid is None:
                raise RuntimeError(f"Parent grid {parents[name]} not defined")
            if "childGrids" not in pgrid:
                pgrid["childGrids"] = []
            pgrid["childGrids"].append(grid)

    ggxfgroup = {
        "ggxfGroups": [
            {
                "ggxfGroupName": grid_file,
                "gridParameters": parameters,
                "interpolationMethod": "bilinear",
                "grids": rootgrids,
            }
        ]
    }
    ggxfyaml = yaml.dump(ggxfgroup, Dumper=yaml.SafeDumper, indent=2)
    ggxfyaml = re.sub(r"([\"\'])(\[[^\]]*\])\1", r"\2", ggxfyaml)

    with open(yaml_file, "w") as outh:
        outh.write(ggxfyaml)


if __name__ == "__main__":
    main()
