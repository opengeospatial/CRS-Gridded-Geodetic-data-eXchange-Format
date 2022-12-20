#!/usr/bin/python3

import argparse
import csv
import json
import logging
import os.path
import numpy as np

from .NetCDF import Reader as NetCdfReader, Writer as NetCdfWriter, NETCDF_OPTIONS
from .YAML import Reader as YamlReader, Writer as YamlWriter, YAML_OPTIONS


def main():
    parser = argparse.ArgumentParser(
        "Read, save, calculate a GGXF file",
        epilog="This is a proof of concept implementation to evaluate encoding options.\n"
        + 'The output is not necessarily an "authoritative" GGXF file\n\n'
        + f"{NETCDF_OPTIONS}\n{YAML_OPTIONS}"
        "",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "ggxf_file", help="Name of GGXF file to load - .yaml for YAML format"
    )
    parser.add_argument(
        "-o",
        "--output-ggxf-file",
        help="Save GGXF to file - .yaml for YAML format",
        metavar="filename",
    )
    parser.add_argument(
        "-n",
        "--netcdf4-option",
        action="append",
        help="Options for NetCDF4 files (see below for options)",
        metavar="option=value",
    )
    parser.add_argument(
        "-y",
        "--yaml-option",
        action="append",
        help="Pptions for YAML files (see below for options)",
        metavar="option=value",
    )

    parser.add_argument(
        "-c",
        "--coord-csv-file",
        help="CSV file of points to calculate - assumes column headers with X, Y columns",
        metavar="csv_filename",
    )
    parser.add_argument(
        "-e",
        "--epoch",
        type=float,
        help="Epoch at which to calculate GGXF",
        metavar="epoch",
    )
    parser.add_argument(
        "--base-epoch",
        type=float,
        help="Base epoch for calculating change between epochs",
        metavar="epoch",
    )
    parser.add_argument(
        "--output-csv-file",
        help="CSV file to convert - assumes column headers with X, Y columns (default based on input)",
        metavar="output_csv_filename",
    )
    parser.add_argument(
        "--csv-decimal-places",
        type=int,
        default=4,
        help="Number of decimal places for CSV calculated values",
        metavar="csv_summary_file",
    )

    parser.add_argument(
        "--csv-summary",
        help="Write a grid summary to the named CSV file",
        metavar="csv_summary_file",
    )
    parser.add_argument(
        "--list-grids", action="store_true", help="Print a list of grids with ids"
    )
    parser.add_argument(
        "--dump-grid",
        nargs=2,
        help="Dump a specific grid to a CSV file (use --list-grids to get grid ids)",
        metavar=("grid_id", "csv_file"),
    )
    parser.add_argument(
        "-g", "--debug", action="store_true", help="Generate debugging output"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="More verbose output"
    )

    args = parser.parse_args()

    logging.basicConfig()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    ggxf_file = args.ggxf_file

    netcdf_options = compileOptions(args.netcdf4_option)
    yaml_options = compileOptions(args.yaml_option)
    if ggxf_file.endswith(".yaml"):
        ggxf = YamlReader.Read(ggxf_file, options=yaml_options)
    elif ggxf_file.endswith(".ggxf"):
        ggxf = NetCdfReader.Read(ggxf_file, options=netcdf_options)
    else:
        raise RuntimeError(
            f"GGXF filename {ggxf_file} must have extension .yaml or .ggxf (NetCDF)"
        )
    if ggxf is None:
        return
    if args.debug:
        ggxf.setDebug()
    if args.csv_summary:
        writeCsvGridSummary(ggxf, args.csv_summary, args.csv_decimal_places)
    if args.list_grids:
        listGrids(ggxf)
    if args.dump_grid:
        gridid, dumpfile = args.dump_grid
        dumpGrid(ggxf, gridid, dumpfile)
    if args.coord_csv_file:
        calculateCsvPoints(
            ggxf,
            args.coord_csv_file,
            args.output_csv_file,
            epoch=args.epoch,
            refepoch=args.base_epoch,
            decimal_places=args.csv_decimal_places,
        )
    if args.output_ggxf_file:
        output_ggxf_file = args.output_ggxf_file
        if output_ggxf_file.endswith(".yaml"):
            YamlWriter.Write(ggxf, output_ggxf_file, options=yaml_options)
        elif output_ggxf_file.endswith(".ggxf"):
            NetCdfWriter.Write(ggxf, output_ggxf_file, options=netcdf_options)
        else:
            raise RuntimeError(
                f"GGXF output filename {output_ggxf_file} must have extension .yaml or .ggxf (NetCDF)"
            )


def compileOptions(source):
    options = {}
    if source is not None:
        for option in source:
            if "=" in option:
                key, value = option.split("=", maxsplit=1)
                options[key] = value
            else:
                options[option] = "true"
    return options


def calculateCsvPoints(
    ggxf, input_csv, output_csv, epoch=None, refepoch=None, decimal_places: int = 4
):

    if not output_csv:
        output_csv = os.path.splitext(input_csv)[0] + "-out.csv"

    ordinates = ggxf.nodeCoordinateParameters()

    with open(input_csv) as inh, open(output_csv, "w") as outh:
        csvin = csv.reader(inh)
        csvout = csv.writer(outh)
        cols = list(next(csvin))
        xcol = None
        ycol = None
        for ncol, col in enumerate(cols):
            if col == ordinates[0]:
                xcol = ncol
            elif col == ordinates[1]:
                ycol = ncol
        if xcol is None or ycol is None:
            logging.error(
                f"Input CSV {input_csv} does not have {' and '.join(ordinates)} columns"
            )
            return
        missingval = []
        for param in ggxf.parameters():
            cols.append(param.name())
            missingval.append("")
        csvout.writerow(cols)
        nrow = 1
        for row in csvin:
            nrow += 1
            try:
                output = list(row)
                xy = [float(row[xcol]), float(row[ycol])]
                value = ggxf.valueAt(xy, epoch, refepoch)
                if value is None:
                    value = missingval
                else:
                    value = [f"{x:.{decimal_places}f}" for x in value]
                output.extend(value)
            except Exception as ex:
                logging.error(f"Error at row {nrow} of {input_csv}: {ex}")
                output = list(row)
                output.extend(missingval)
                output.append(f"{ex}")
            csvout.writerow(output)


def writeCsvGridSummary(ggxf, csv_summary_file, decimal_places=4):
    csvcols = [
        "id",
        "ggxfGroupName",
        "ggxfGridName",
        "parentId",
        "gridPriority",
        "iCodeCount",
        "jNodeCount",
        "depth",
        "extent_wkt",
    ]
    param0 = len(csvcols)
    params = {}
    empty = []
    for param in ggxf.parameters():
        name = param.name()
        params[name] = param0
        param0 += 2
        csvcols.append(f"{name}-min")
        csvcols.append(f"{name}-max")
        empty.extend(["", ""])
    with open(csv_summary_file, "w") as csvh:
        csvw = csv.writer(csvh)
        csvw.writerow(csvcols)
        for group in ggxf.groups():
            groupname = group.name()
            for grid in group.allgrids():
                size = grid.size()
                extents = grid.extents()
                xmin = str(extents[0][0])
                xmax = str(extents[1][0])
                ymin = str(extents[0][1])
                ymax = str(extents[1][1])
                # Assume X=lat, Y=lon so swap axes for preferred lon,lat!
                wkt = f"POLYGON(({ymin} {xmin},{ymin} {xmax},{ymax} {xmax},{ymax} {xmin}, {ymin} { xmin}))"
                depth = 1
                pgrid = grid
                while pgrid.parent() is not None:
                    depth += 1
                    pgrid = pgrid.parent()
                summary = grid.summary()
                gridparams = summary["parameters"]
                priority = grid.priority()
                priority = str(priority) if priority is not None else ""
                parentid = grid.parent().id() if grid.parent() else ""
                csvrow = [
                    grid.id(),
                    groupname,
                    grid.name(),
                    parentid,
                    grid.priority(),
                    str(size[0]),
                    str(size[1]),
                    depth,
                    wkt,
                ]
                csvrow.extend(empty)
                for param, minmax in gridparams.items():
                    if param in params:
                        csvrow[params[param]] = f"{minmax['min']:.{decimal_places}f}"
                        csvrow[
                            params[param] + 1
                        ] = f"{minmax['max']:.{decimal_places}f}"
                csvw.writerow(csvrow)


def listGrids(ggxf):
    for grid in ggxf.allgrids():
        print(f"{grid.id()}: {grid.name()}")


def dumpGrid(ggxf, gridid, dumpfile):
    # Want to handle also gridid="extents" to create WKT bounding boxes
    # Need to handle output of parameters for groups with different parameter lists.
    dgrid = None
    grids = list(ggxf.allgrids())
    if gridid != "all":
        allgrids = grids
        grids = []
        for grid in allgrids:
            if grid.id() == gridid or grid.name() == gridid:
                grids.append(grid)
                break
        if not grids:
            print(f"Grid {gridid} not defined in GGXF file")
            return
    with open(dumpfile, "w") as csvh:
        csvw = csv.writer(csvh)
        fields = ["X", "Y", "i", "j"]
        addid = False
        if len(grids) > 1:
            addid = True
            fields.insert(0, "id")
        empty = []
        fieldid = {}
        for grid in grids:
            for pname in grid.group().parameterNames():
                if pname not in fields:
                    fieldid[pname] = len(fields)
                    fields.append(pname)
                    empty.append("")
        csvw.writerow(fields)
        for id, grid in enumerate(grids):
            imax, jmax = grid.maxij()
            data = grid.data()
            gridid = str(id)
            valcols = [fieldid[pname] for pname in grid.group().parameterNames()]
            for jnode in range(jmax + 1):
                for inode in range(imax + 1):
                    xy = grid.calcxy([inode, jnode])
                    vals = data[jnode, inode]
                    row = [str(c) for c in xy]
                    row.append(str(inode))
                    row.append(str(jnode))
                    if addid:
                        row.insert(0, gridid)
                    row.extend(empty)
                    for vcol, val in zip(valcols, vals):
                        row[vcol] = val
                    csvw.writerow(row)


if __name__ == "__main__":
    main()
