#!/usr/bin/python3

import argparse
import csv
import logging
import os.path
import sys
import re

from .NetCDF import (
    Reader as NetCdfReader,
    Writer as NetCdfWriter,
    NETCDF_READ_OPTIONS,
    NETCDF_WRITE_OPTIONS,
)
from .YAML import (
    Reader as YamlReader,
    Writer as YamlWriter,
    YAML_READ_OPTIONS,
    YAML_WRITE_OPTIONS,
)

from .GdalImport import (
    GdalImporter,
    EpsgCacheFileEnv,
    GdalDriverConfigFileEnv,
    GdalDriverConfigFile,
)

from .Constants import *

CMDARG_CONVERT = "convert"
CMDARG_IMPORT = "import"
CMDARG_DESCRIBE = "describe"
CMDARG_CALCULATE = "calculate"

# Other possible arguments are "validate", "extract"


def main():
    rootParser = argparse.ArgumentParser(
        description="Read, save, calculate a GGXF file",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = rootParser.add_subparsers(
        help="Subcommand help", dest="command", required=True
    )

    for addparser in (
        addConvertParser,
        addDescribeParser,
        addCalculateParser,
        addImportParser,
    ):
        parser = addparser(subparsers)
        addLoggingArguments(parser)

    try:
        args = rootParser.parse_args()
        setLogLevel(args)
        args.function(args)
    except Exception as ex:
        print(f"Failed: {ex}")
        sys.exit(1)


#####################################################################################
# Common arguments and handlers


def addInputGgxfArguments(parser):

    parser.add_argument(
        "input_ggxf_file", help="Input GGXF file, either .yaml or .ggxf"
    )


def addOutputGgxfArguments(parser):
    parser.add_argument(
        "output_ggxf_file", help="Output GGXF file, either .yaml or .ggxf"
    )


def addFormatOptionArguments(parser):
    parser.add_argument(
        "-n",
        "--netcdf4-options",
        action="append",
        metavar="option=value",
        help="Format options for NetCDF4 files",
    )
    parser.add_argument(
        "-y",
        "--yaml-options",
        action="append",
        metavar="option=value",
        help="Format options for YAML files",
    )


def compileFormatOptions(source):
    options = {}
    if source is not None:
        for option in source:
            if "=" in option:
                key, value = option.split("=", maxsplit=1)
                options[key] = value
            else:
                options[option] = "true"
    return options


def inputFileOptions():
    return f"""
Format options for reading a YAML GGXF file can be
{YAML_READ_OPTIONS}

Format options for reading a NetCDF4 GGXF file can be
{NETCDF_READ_OPTIONS}
    """


def outputFileOptions():
    return f"""
Format options for writing a YAML GGXF file can be:
{YAML_WRITE_OPTIONS}

Format options for writing a NetCDF4 GGXF file can be:
{NETCDF_WRITE_OPTIONS}
    """


def loadGgxfInputFile(args):
    ggxf_file = args.input_ggxf_file
    if ggxf_file.endswith(".yaml"):
        yaml_options = compileFormatOptions(args.yaml_options)
        ggxf = YamlReader.Read(ggxf_file, options=yaml_options)
    elif ggxf_file.endswith(".ggxf"):
        netcdf_options = compileFormatOptions(args.netcdf4_options)
        ggxf = NetCdfReader.Read(ggxf_file, options=netcdf_options)
    else:
        raise RuntimeError(
            f"GGXF filename {ggxf_file} must have extension .yaml or .ggxf (NetCDF)"
        )
    return ggxf


def saveGgxfOutputFile(ggxf, args):
    output_ggxf_file = args.output_ggxf_file
    if output_ggxf_file.endswith(".yaml"):
        yaml_options = compileFormatOptions(args.yaml_options)
        YamlWriter.Write(ggxf, output_ggxf_file, options=yaml_options)
    elif output_ggxf_file.endswith(".ggxf"):
        netcdf_options = compileFormatOptions(args.netcdf4_options)
        NetCdfWriter.Write(ggxf, output_ggxf_file, options=netcdf_options)
    else:
        raise RuntimeError(
            f"GGXF output filename {output_ggxf_file} must have extension .yaml or .ggxf (NetCDF)"
        )


def addLoggingArguments(parser):
    parser.add_argument(
        "-g", "--debug", action="store_true", help="Generate debugging output"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="More verbose output"
    )


def setLogLevel(args):
    logging.basicConfig()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)


#####################################################################################
# Convert a GGXF file


def addConvertParser(subparsers):
    parser = subparsers.add_parser(
        CMDARG_CONVERT,
        description="Convert between YAML and NetCDF formats",
        epilog=f"{inputFileOptions()}\n{outputFileOptions()}",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    addInputGgxfArguments(parser)
    addOutputGgxfArguments(parser)
    addFormatOptionArguments(parser)
    parser.set_defaults(function=convertGgxf)
    return parser


def convertGgxf(args):
    ggxf = loadGgxfInputFile(args)
    saveGgxfOutputFile(ggxf, args)


#####################################################################################
# Describe a GGXF file


def addDescribeParser(subparsers):
    parser = subparsers.add_parser(
        CMDARG_DESCRIBE,
        description="Describe a GGXF file",
        epilog=inputFileOptions(),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    addInputGgxfArguments(parser)
    addFormatOptionArguments(parser)
    parser.add_argument(
        "-c",
        "--csv-grid-summary",
        metavar="filename",
        help="Write a CSV file containing a summary of grids",
    )
    parser.add_argument(
        "-d",
        "--coordinate-decimal-places",
        type=int,
        default=8,
        metavar="#",
        help="Number of decimal places for coordinates",
    )
    parser.add_argument(
        "-p",
        "--parameter-decimal-places",
        type=int,
        default=4,
        metavar="#",
        help="Number of decimal places for values in summary file",
    )
    parser.set_defaults(function=describeGgxf)
    return parser


def describeGgxf(args):
    ggxf = loadGgxfInputFile(args)
    printGgxfFileSummary(ggxf)
    if args.csv_grid_summary:
        writeCsvGridSummary(
            ggxf,
            args.csv_grid_summary,
            args.coordinate_decimal_places,
            args.parameter_decimal_places,
        )


def printGgxfFileSummary(ggxf):
    print(
        f"""
GGXF file: {ggxf.metadata('filename')}
Content type: {ggxf.contentType()}
Parameters: {", ".join((p.name() for p in ggxf.parameters()))}
interpolation CRS: {crsWktSummary(ggxf.metadata(GGXF_ATTR_INTERPOLATION_CRS_WKT))}
source CRS: {crsWktSummary(ggxf.metadata(GGXF_ATTR_SOURCE_CRS_WKT))}
target CRS: {crsWktSummary(ggxf.metadata(GGXF_ATTR_TARGET_CRS_WKT))}
extent: {extentDescription(ggxf)}
ggxfGroups: {len(list(ggxf.groups()))}
grids: {len(list(ggxf.allgrids()))}
"""
    )


def extentDescription(ggxf):
    extents = ggxf.metadata(GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT)
    bboxobj = extents.get(GGXF_ATTR_BOUNDING_BOX, {})
    bbox = [
        bboxobj[k]
        for k in (
            GGXF_ATTR_SOUTH_BOUND_LATITUDE,
            GGXF_ATTR_NORTH_BOUND_LATITUDE,
            GGXF_ATTR_EAST_BOUND_LONGITUDE,
            GGXF_ATTR_WEST_BOUND_LONGITUDE,
        )
    ]
    description = extents.get(GGXF_ATTR_EXTENT_DESCRIPTION, "")
    bbox_extent = f"Latitude {bbox[0]} - {bbox[1]}, Longitude {bbox[2]} - {bbox[3]}"
    return f"{description} {bbox_extent}".strip()


def crsWktSummary(wkt):
    if wkt is None:
        return ""
    name = ""
    if match := re.match(r"\w+\s*\[\s*\"([^\"]+)\"", wkt):
        name = match.group(1)
    if match := re.search(r"ID\s*\[\s*\"EPSG\"\s*\,\s*(\d+)[\s\]]*$", wkt):
        name = f"{name} EPSG:{match.group(1)}"
    return name.strip()


def writeCsvGridSummary(ggxf, csv_summary_file, coord_ndp=8, param_ndp=4):
    csvcols = [
        "id",
        "ggxfGroupName",
        "ggxfGridName",
        "parentId",
        "gridPriority",
        "iCodeCount",
        "jNodeCount",
        "depth",
        "xmin",
        "xmax",
        "ymin",
        "ymax",
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
    csvcols.append("extent_wkt")
    formatcrd = f"{0:.{coord_ndp}}".format
    formatprm = f"{0:.{param_ndp}}".format
    with open(csv_summary_file, "w") as csvh:
        csvw = csv.writer(csvh)
        csvw.writerow(csvcols)
        for group in ggxf.groups():
            groupname = group.name()
            for grid in group.allgrids():
                size = grid.size()
                extents = grid.extents()
                xmin = formatcrd(extents[0][0])
                xmax = formatcrd(extents[1][0])
                ymin = formatcrd(extents[0][1])
                ymax = formatcrd(extents[1][1])
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
                    xmin,
                    xmax,
                    ymin,
                    ymax,
                ]
                csvrow.extend(empty)
                for param, minmax in gridparams.items():
                    if param in params:
                        csvrow[params[param]] = formatprm(minmax["min"])
                        csvrow[params[param] + 1] = formatprm(minmax["max"])
                csvrow.append(wkt)
                csvw.writerow(csvrow)
    print(f"Grid summary written to {csv_summary_file}")


#####################################################################################
# Calculate parameters on a GGXF file


def addCalculateParser(subparsers):
    parser = subparsers.add_parser(
        CMDARG_CALCULATE,
        description="Calculate parameters from a GGXF file",
        epilog=f"""
The input CSV file must have a header row of field names.  The input
coordinate are in columns nodeLatitude, nodeLongitude, or if the 
interpolationCrs is a projection CRS then nodeEasting, nodeNorthing.

{inputFileOptions()}"
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    addInputGgxfArguments(parser)
    addFormatOptionArguments(parser)
    parser.add_argument(
        "csv_points_file",
        metavar="filename",
        help="Input CSV file of point coordinates",
    )
    parser.add_argument("csv_results_file", metavar="filename", help="Results CSV file")
    parser.add_argument(
        "-d",
        "--csv-decimal-places",
        type=int,
        default=4,
        metavar="#",
        help="Number of decimal places for CSV calculated values",
    )
    parser.add_argument(
        "-e",
        "--epoch",
        type=float,
        help="Epoch in years at which to calculate GGXF",
        metavar="####.#",
    )
    parser.add_argument(
        "-b",
        "--base-epoch",
        type=float,
        help="Base epoch in years for calculating change between epochs",
        metavar="####.#",
    )
    parser.set_defaults(function=calculateGgxf)
    return parser


def calculateGgxf(args):
    ggxf = loadGgxfInputFile(args)
    input_csv = args.csv_points_file
    output_csv = args.csv_results_file
    decimal_places = args.csv_decimal_places
    epoch = args.epoch
    refepoch = args.base_epoch
    calculateCsvPoints(ggxf, input_csv, output_csv, epoch, refepoch, decimal_places)


def calculateCsvPoints(
    ggxf, input_csv, output_csv, epoch=None, refepoch=None, decimal_places: int = 4
):
    if not os.path.isfile(input_csv):
        raise RuntimeError(f"CSV input file {input_csv} not found")

    with open(input_csv) as inh, open(output_csv, "w") as outh:
        csvin = csv.reader(inh)
        csvout = csv.writer(outh)
        cols = list(next(csvin))
        xcol = None
        ycol = None
        coordFields = ggxf.nodeCoordinateParameters()
        for ncol, col in enumerate(cols):
            if col == coordFields[0]:
                xcol = ncol
            elif col == coordFields[1]:
                ycol = ncol
        if xcol is None or ycol is None:
            logging.error(
                f"Input CSV {input_csv} does not have {' and '.join(coordFields)} columns"
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


#####################################################################################
# Import gridded data to a GGXF file

ImportHelp = f"""
Basic usage:
    ggxf {CMDARG_IMPORT} meta_template.yaml
        Creates a metadata template file meta_template.yaml

    ggxf {CMDARG_IMPORT} -w meta_file.yaml grid_file
        Includes metadata template including attributes from grid file.

    ggxf {CMDARG_IMPORT} ggxf_file.yaml grid_file
        Creates a GGXF file to import data from the grid file.

    ggxf {CMDARG_CONVERT} ggxf_file.yaml ggxf_file.ggxf
        Convert the YAML GGXF file to NetCDF

The {CMDARG_IMPORT} may include one or more input template files using
the -m option.  Each of these will be used in turn to update attributes 
in the output YAML file. After these are applied any attributes specified
by -a will be applied.  If -p is specified then attributes not explicitly 
set will be included in the ggxf_file.yaml with placeholder values, otherwise
they are omitted.

Some GDAL drivers have specific content types and parameter definitions (eg
NTv2).  These may be configured in a YAML file identified by an environment
variable {GdalDriverConfigFileEnv}.

The interpolation, source, and target CRS may be specified as EPSG:####.  The 
EPSG API will be queried to retrieve the full CRS WKT specification.  The 
WKT strings can be cached in a JSON file specified by environment 
variable {EpsgCacheFileEnv}.

GDAL driver config file: {GdalDriverConfigFile}
"""


def addImportParser(subparsers):
    parser = subparsers.add_parser(
        CMDARG_IMPORT,
        description="Import GDAL supported grid formats to GGXF",
        epilog=ImportHelp,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "yaml_file", help="Output YAML file - GGXF or metadata template"
    )
    parser.add_argument(
        "grid_file",
        nargs="?",
        help="Grid file to import (if not supplied just write a template)",
    )
    parser.add_argument(
        "-m",
        "--metadata-file",
        action="append",
        help="Input file of metadata (may be repeated)",
    )
    parser.add_argument("-c", "--content-type", help="GGXF content type of grid")
    parser.add_argument(
        "-a",
        "--attribute",
        action="append",
        help="GGXF file attribute written as attribute=value",
    )
    parser.add_argument(
        "-w",
        "--write-template",
        action="store_true",
        help="Write metadata template to YAML file instead of GGXF",
    )
    parser.add_argument(
        "-p",
        "--include-placeholders",
        action="store_true",
        help="Include placeholder metadata in output GGXF YAML",
    )
    parser.set_defaults(function=importGgxf)
    return parser


def importGgxf(args):
    yaml_file = args.yaml_file
    if not yaml_file.endswith(".yaml"):
        raise RuntimeError(f'YAML filename ({yaml_file}) must end with ".yaml"')

    attrargs = args.attribute or []
    attributes = {}
    for attr in attrargs:
        match = re.match(r"(\w+)\=(.+)", attr)
        if not match:
            raise RuntimeError(
                f'--attribute parameter {attr} must be formatted as "attribute=value"'
            )
        attributes[match.group(1)] = match.group(2)

    GdalImporter.Import(
        args.yaml_file,
        args.grid_file,
        args.metadata_file,
        attributes=attributes,
        write_template=args.write_template,
        content_type=args.content_type,
        include_placeholders=args.include_placeholders,
    )


if __name__ == "__main__":
    main()
