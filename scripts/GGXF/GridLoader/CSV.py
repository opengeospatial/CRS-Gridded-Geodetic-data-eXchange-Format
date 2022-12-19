#!/usr/bin/python3
#
# Provides a more generic form of ggxf-csv data source allowing customised
# field names.

import os.path
from .ggxf_csv import LoadCsvGrid, CsvLoaderError, GGXF_CSV_FILENAME_ATTR

# from ..Constants import *

CSV_FILENAME_ATTR = GGXF_CSV_FILENAME_ATTR
CSV_INTERPOLATION_COORD_ATTR = "interpolationCoordFields"
CSV_PARAMETER_FIELDS_ATTR = "parameterFields"

CSV_GRID_TOLERANCE_FACTOR = 0.00001

HELP = f"""
CSV grid loader for GGXF YAML format.  Assumes a comma separated CSV file
with a header line containing the field names. 

The data must be ordered following rows and columns in the grid.

Datasource attributes:

  {CSV_FILENAME_ATTR}: filename
     The name of the CSV file to load

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
    xyfields = datasource.get(CSV_INTERPOLATION_COORD_ATTR, [])
    if not isinstance(xyfields, list) or len(xyfields) not in (0, 2):
        raise CsvLoaderError(
            f"{CSV_INTERPOLATION_COORD_ATTR} fields must be a list of two values"
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
        filename, datafields, xyfields=xyfields, xyoptional=xyoptional, logger=logger
                    )
