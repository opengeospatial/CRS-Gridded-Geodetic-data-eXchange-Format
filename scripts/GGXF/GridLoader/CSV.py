#!/usr/bin/python3
#
# Provides a more generic form of ggxf-csv data source allowing customised
# field names.

import os.path

from .ggxf_csv import (
    GGXF_CSV_FILENAME_ATTR,
    GGXF_CSV_SEPARATOR_ATTR,
    GGXF_CSV_SEPARATORS,
    GGXF_CSV_DEFAULT_SEPARATOR,
    GGXF_CSV_SEPARATORS_TEXT,
    CsvLoaderError,
    LoadCsvGrid,
)

# from ..Constants import *

CSV_FILENAME_ATTR = GGXF_CSV_FILENAME_ATTR
CSV_SEPARATOR_ATTR = GGXF_CSV_SEPARATOR_ATTR
CSV_INTERPOLATION_COORD_ATTR = "nodeCoordinateFields"
CSV_PARAMETER_FIELDS_ATTR = "parameterFields"
CSV_HEADER_LINES_ATTR = "headerLines"
CSV_FIELD_NAMES_ATTR = "fieldNames"

CSV_GRID_TOLERANCE_FACTOR = 0.00001

HELP = f"""
CSV grid loader for GGXF YAML format.  Assumes a comma separated CSV file
with a header line containing the field names. 

The data must be ordered following rows and columns in the grid.

Datasource attributes:

  {CSV_FILENAME_ATTR}: filename
     The name of the CSV file to load

  {CSV_SEPARATOR_ATTR}: {GGXF_CSV_SEPARATORS_TEXT}
     Field separator in the file

  {CSV_HEADER_LINES_ATTR}: nlines
     The number of header lines at the top of the CSV file to skip before reading data

  {CSV_FIELD_NAMES_ATTR}: [ "field1", "field2", ... ]
     The names of the fields in the CSV file.  If this is not supplied then field names
     will be read from the first line of the file after the header lines

  {CSV_INTERPOLATION_COORD_ATTR}: [ "latitude", "longitude" ]
     Array specifying the fields containing the interpolation coordinate axes

  {CSV_PARAMETER_FIELDS_ATTR}: ["param1", "param2" ]
     Array specifying the names of fields defining parameters at grid nodes.

"""


def LoadGrid(group, datasource, logger):
    for attr in (
        CSV_FILENAME_ATTR,
        CSV_INTERPOLATION_COORD_ATTR,
        CSV_PARAMETER_FIELDS_ATTR,
    ):
        if attr not in datasource:
            raise CsvLoaderError(f"CSV data source missing {attr} attribute")

    filename = datasource.get(CSV_FILENAME_ATTR)
    if not os.path.isfile(filename):
        raise CsvLoaderError(f"CSV file {filename} not found")

    headerlines = datasource.get(CSV_HEADER_LINES_ATTR, 0)
    try:
        headerlines = int(headerlines)
    except ValueError:
        raise CsvLoaderError(f"{CSV_HEADER_LINES_ATTR} must be an integer")

    fieldnames = datasource.get(CSV_FIELD_NAMES_ATTR)
    if fieldnames is not None and not isinstance(fieldnames, list):
        raise CsvLoaderError(f"{CSV_FIELD_NAMES_ATTR} must be a list of values")

    separator = datasource.get(CSV_SEPARATOR_ATTR, GGXF_CSV_DEFAULT_SEPARATOR)
    if separator not in GGXF_CSV_SEPARATORS:
        raise CsvLoaderError(
            f"CSV data source attribute {CSV_SEPARATOR_ATTR} value {separator} invalid: "
            f"Must be one of {', '.join(sorted(GGXF_CSV_SEPARATORS.keys()))}"
        )
    delimiter=GGXF_CSV_SEPARATORS[separator]

    xyfields = datasource.get(CSV_INTERPOLATION_COORD_ATTR, [])
    if not isinstance(xyfields, list) or len(xyfields) not in (0, 2):
        raise CsvLoaderError(
            f"{CSV_INTERPOLATION_COORD_ATTR} must be a list of two values"
        )

    xyoptional = True
    if xyfields == []:
        xyfields = group.ggxf().nodeCoordinateParameters()
        xyoptional = True
    datafields = datasource.get(CSV_PARAMETER_FIELDS_ATTR)
    if datafields is None:
        datafields = group.parameterNames()
    elif isinstance(datafields, str):
        datafields = [datafields]
    if not isinstance(datafields, list):
        raise CsvLoaderError(
            f"{CSV_PARAMETER_FIELDS_ATTR} fields must be a list of values"
        )

    return LoadCsvGrid(
        filename,
        datafields,
        xyfields=xyfields,
        xyoptional=xyoptional,
        fieldnames=fieldnames,
        headerlines=headerlines,
        delimiter=delimiter,
        logger=logger,
    )
