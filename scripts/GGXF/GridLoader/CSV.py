#!/usr/bin/python3

import numpy as np
import os.path
import logging
import csv

# from ..Constants import *

CSV_FILENAME_ATTR = "csvFilename"
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


class CsvLoaderError(RuntimeError):
    pass


def LoadGrid(group, datasource, logger):
    if logger is None:
        logger = logging.getLogger()
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
    xyfields = datasource.get(CSV_INTERPOLATION_COORD_ATTR)
    if not isinstance(xyfields, list) or len(xyfields) != 2:
        raise CsvLoaderError(
            f"{CSV_INTERPOLATION_COORD_ATTR} fields must be a list of two values"
        )
    datafields = datasource.get(CSV_PARAMETER_FIELDS_ATTR)
    if not isinstance(datafields, list):
        raise CsvLoaderError(
            f"{CSV_PARAMETER_FIELDS_ATTR} fields must be a list of values"
        )

    try:
        with open(filename, "r", encoding="utf-8-sig") as csvh:
            csvr = csv.reader(csvh)
            fields = csvr.__next__()
            fldids = []
            for field in [*xyfields, *datafields]:
                if field not in fields:
                    raise CsvLoaderError(
                        f"Field {field} is missing in CSV file {filename}"
                    )
                fldids.append(fields.index(field))

            data = []
            nj = 0
            for row in csvr:
                nj += 1
                try:
                    data.append([float(row[fld]) for fld in fldids])
                except IndexError:
                    raise CsvLoaderError(
                        f"Not enough columns at line {nj} of CSV file {filename}"
                    )
                except ValueError:
                    raise CsvLoaderError(
                        f"Non numeric value at line {nj} of CSV file {filename}"
                    )
    except CsvLoaderError:
        raise
    except:
        raise CsvLoaderError(f"Cannot open CSV grid file {filename}")

    data = np.array(data)
    xy = data[:, :2]
    dxy = xy[1:, :] - xy[:-1, :]
    reverse = ((dxy[:, 0] * dxy[0, 0] + dxy[:, 1] * dxy[0, 1]) < 0.0).nonzero()[0] + 1
    ni = reverse[0]
    nj = reverse.size + 1
    test = np.arange(1, nj) * ni
    if any(reverse != test):
        sr = set(reverse)
        st = set(test)
        badrow = min(sr ^ st)
        raise CsvLoaderError(
            f"CSV file {filename} doesn't contain a regular grid at line {badrow+2} - expecting new grid row every {ni} lines"
        )

    if data.shape[0] != nj * ni:
        raise CsvLoaderError(
            f"CSV file {filename} doesn't contain a regular grid - expect {ni}x{nj}={ni*nj} rows"
        )

    # Calculate affine coefficients assuming grid is aligned with axes
    xy = xy.reshape(nj, ni, 2)
    xy0 = xy[0, 0]
    ddj = (xy[nj - 1, 0] - xy0) / (nj - 1)
    ddi = (xy[0, ni - 1] - xy0) / (ni - 1)

    # Compare the node coordinates with the values calculated from the indices to
    # see if the nodes are on the inferred grid.
    ij = np.indices((nj, ni))
    tmat = np.vstack((ddj, ddi))
    calc = np.tensordot(tmat.T, ij, axes=[[1], [0]])
    calc = np.moveaxis(calc, 0, -1) + xy0
    maxerr = np.max(np.abs(xy - calc))
    tolerance = np.sqrt(np.sum(tmat * tmat)) * CSV_GRID_TOLERANCE_FACTOR
    if maxerr > tolerance:
        raise CsvLoaderError(
            f"Grid nodes in {filename} are not ordered in a regular grid aligned with the coordinate axes (maximum coordinate error {maxerr} units)"
        )

    # Compile the affine coefficients and grid nodes as expected by the YAML GGXF reader

    affine = np.array([xy0[0], ddi[0], ddj[0], xy0[1], ddi[1], ddj[1]]).tolist()
    gridData = data[:, 2:]
    gridData = gridData.reshape(nj, ni, gridData.shape[1])
    size = (int(ni), int(nj))
    logger.debug(f"CsvLoader: Loaded {filename}")
    logger.debug(f"CsvLoader: size {size}")
    logger.debug(f"CsvLoader: affine coeffs {affine}")
    logger.debug(f"CsvLoader: Grid loaded with shape {gridData.shape}")
    return (size, affine, gridData)
