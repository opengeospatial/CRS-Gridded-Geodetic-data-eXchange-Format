#!/usr/bin/python3
#
# ggxf-csv loader for GGXF.  Expected to return an array of (nj,ni,np) or a column major flattening of it.
# (ie (rows,cols, params))

import csv
import logging
import os.path

import numpy as np

from ..Constants import *

# from ..Constants import *

GGXF_CSV_FILENAME_ATTR = "gridFilename"
GGXF_CSV_SEPARATOR_ATTR = "separator"

SEPARATOR_COMMA = "comma"
SEPARATOR_SPACE = "space"
SEPARATOR_TAB = "tab"

GGXF_CSV_DEFAULT_SEPARATOR = SEPARATOR_COMMA

GGXF_CSV_SEPARATORS = {SEPARATOR_COMMA: ",", SEPARATOR_SPACE: " ", SEPARATOR_TAB: "\t"}


GGXF_CSV_GRID_TOLERANCE_FACTOR = 0.00001

HELP = f"""
ggxf-csv grid loader for GGXF YAML format.  Assumes a comma separated ggxf-csv file
with a header line containing the field names. 

The data must be ordered following rows and columns in the grid.

Datasource attributes:

  {GGXF_CSV_FILENAME_ATTR}: filename
     The name of the ggxf-csv file to load

  {GGXF_CSV_SEPARATOR_ATTR}: "{SEPARATOR_COMMA}", "{SEPARATOR_SPACE}", or "{SEPARATOR_TAB}"
     Definition of the separator character used in the ggxf-csv file

"""


class CsvLoaderError(RuntimeError):
    pass


class SpaceDelimitedFile:
    """
    Class for space delimited files - not using csv.reader as this
    should robustly handle extra space characters in the file.
    """

    def __init__(self, fh):
        self._fh = fh

    def __next__(self):
        data = self.readline()
        if data == "":
            raise StopIteration
        return data.split()


def LoadGrid(group, datasource, logger):

    for attr in (GGXF_CSV_FILENAME_ATTR,):
        if attr not in datasource:
            raise CsvLoaderError(f"CSV data source missing {attr} attribute")
    separator = datasource.get(GGXF_CSV_SEPARATOR_ATTR, GGXF_CSV_DEFAULT_SEPARATOR)
    if separator not in GGXF_CSV_SEPARATORS:
        raise CsvLoaderError(
            f"CSV data source attribute {GGXF_CSV_SEPARATOR_ATTR} value {separator} invalid: "
            f"Must be one of {', '.join(sorted(GGXF_CSV_SEPARATORS.keys()))}"
        )

    delimiter = GGXF_CSV_SEPARATORS[separator]
    filename = datasource.get(GGXF_CSV_FILENAME_ATTR)

    xyfields = group.ggxf().nodeCoordinateParameters()
    datafields = group.parameterNames()
    return LoadCsvGrid(
        filename,
        datafields,
        xyfields=xyfields,
        xyoptional=True,
        logger=logger,
        delimiter=delimiter,
    )


def LoadCsvGrid(
    filename, datafields, xyfields=None, xyoptional=False, logger=None, delimiter=","
):
    if logger is None:
        logger = logging.getLogger()
    if not os.path.isfile(filename):
        raise CsvLoaderError(f"CSV file {filename} not found")
    xyfields = xyfields or []
    haveXyFields = bool(xyfields)
    try:
        with open(filename, "r", encoding="utf-8-sig") as csvh:
            if delimiter == " ":
                csvr = SpaceDelimitedFile(csvh)
            else:
                csvr = csv.reader(csvh, delimiter=delimiter)
            fields = csvr.__next__()

            # If xyfields are optional then ignore missing ordinates if they are not supplied.
            if xyoptional:
                for field in xyfields:
                    if field not in fields:
                        logger.warning(
                            f"CSV file {filename} does not contain node coordinates - affine transformation not checked"
                        )
                        xyfields = []
                        haveXyFields = False
                        break
            # Get the field indexes for the columns of interest
            fldids = []
            for field in (*xyfields, *datafields):
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

    # If we don't have xyfields then all we can do is return the data

    if not haveXyFields:
        return (data, None, None)

    # Otherwise we can infer the affine transformation and grid shape
    # This will be used by the YAML loader to validate the CSV file against
    # the grid affine transformations and i and j counts.

    # Note that the YAML CSV format assumes that the CSV file will be
    # organised as a grid of dimensions [nj,ni,np] in row major order.

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
    xy0 = xy[0]
    ddi = (xy[ni - 1] - xy0) / (ni - 1)
    ddj = (xy[(nj - 1) * ni] - xy0) / (nj - 1)

    # Compare the node coordinates with the values calculated from the indices to
    # see if the nodes are on the inferred grid.
    ij = np.indices((nj, ni)).reshape((2, ni * nj)).T[:, [1, 0]]
    tmat = np.vstack((ddi, ddj))
    calc = ij.dot(tmat) + xy0
    maxerr = np.max(np.abs(xy - calc))
    tolerance = np.sqrt(np.sum(tmat * tmat)) * GGXF_CSV_GRID_TOLERANCE_FACTOR
    if maxerr > tolerance:
        raise CsvLoaderError(
            f"Grid nodes in {filename} are not ordered in a regular grid aligned with the coordinate axes (maximum coordinate error {maxerr} units)"
        )

    # Compile the affine coefficients and grid nodes as expected by the YAML GGXF reader

    affine = np.array([xy0[0], ddi[0], ddj[0], xy0[1], ddi[1], ddj[1]]).tolist()
    gridData = data[:, 2:]
    gridData = gridData.reshape(nj, ni, gridData.shape[1])
    shape = (ni, nj)

    # Calculated shape of grid (ni,nj)
    logger.debug(f"CsvLoader: Loaded {filename}")
    logger.debug(f"CsvLoader: affine coeffs {affine}")
    logger.debug(f"CsvLoader: Grid loaded with shape {shape}")
    return (gridData, shape, affine)
