#!/usr/bin/python3

from osgeo import gdal
import numpy as np
import logging
from ..Constants import *

GDAL_SOURCE_LIST_ATTR = "gdalSourceList"
GDAL_SOURCE_ATTR = "gdalSource"
GDAL_BANDS_ATTR = "selectBands"

HELP = f"""
GDAL grid loader for YAML GGXF files.

Datasource attributes:

{GDAL_SOURCE_LIST_ATTR}: [ sourcedefinitions ]
    If the grid source is collected from multiple data sources then 
    this is followed by a list of entries using {GDAL_SOURCE_ATTR} and
    {GDAL_BANDS_ATTR}.  These must have the same grid definition and affine
    transformation.  The parameters required by the group are collected from
    the bands of each source in turn.

{GDAL_SOURCE_ATTR}: "sourcedefinition"
    Defines the GDAL data source that will be used by the driver.  
    This may be a simple filename if it is recognized by the 
    datasource.  May select a dataset for file containing 
    multiple data sets.  Use gdalinfo to get source definitions.

{GDAL_BANDS_ATTR}: [1,0]
    (Optional) Array defining the 0 based integer indices of bands
    to select from the data source.  Default is all bands.

"""

# Arbitrary tolerance
GDAL_AFFINE_TOLERANCE = 1.0e-10


class GdalLoaderError(RuntimeError):
    pass


def LoadGrid(group, datasource, logger):
    if logger is None:
        logger = logging.getLogger()
    if GDAL_SOURCE_LIST_ATTR in datasource:
        sources = datasource[GDAL_SOURCE_LIST_ATTR]
        logger.debug("Loading grid from list of GDAL data sources")
    else:
        sources = [datasource]

    gridaffine = None
    gridsize = None
    griddata = []

    for source in sources:
        gdalsource = datasource.get(GDAL_SOURCE_ATTR)
        if gdalsource is None:
            raise GdalLoaderError(f"{GDAL_SOURCE_ATTR} attribute is missing")
        logger.debug(f"Loading GDAL data from {gdalsource}")
        dataset = gdal.Open(gdalsource)

        if not dataset:
            raise GdalLoaderError(f"Failed to load GDAL data source {gdalsource}")

        size = (int(dataset.RasterXSize), int(dataset.RasterYSize))
        if gridsize is None:
            gridsize = size
        elif size != gridsize:
            raise GdalLoaderError(
                f"Listed grid data sources have different row/col counts"
            )

        affine = [float(c) for c in dataset.GetGeoTransform()]
        # Convert raster to point georeferencing
        affine[0] += affine[1] / 2.0
        affine[3] += affine[5] / 2.0
        # Check the data to CRS mapping and adjust affine if swapped.
        mapping = dataset.GetSpatialRef().GetDataAxisToSRSAxisMapping()

        if mapping[0] == 2:  # Assume starts either 1,2 or 2,1
            affine = [*affine[3:6], *affine[0:3]]

        if gridaffine is None:
            gridaffine = affine
        else:
            error = np.max(np.abs(np.array(affine), np.array(gridaffine)))
            if error > GDAL_AFFINE_TOLERANCE:
                raise GdalLoaderError(
                    f"Listed grid data sources have different affine coefficents"
                )

        # NOTE: GDAL ReadAsArray returns elements in order p,j,i relative t multipliers
        #  1,i,j used GetGeoTransform.  T.

        data = dataset.ReadAsArray()
        if len(data.shape) == 2:
            shape = (1, *data.shape)
            data = data.reshape(shape)

        # Handle potential reordering of parameters (?)
        if GDAL_BANDS_ATTR in datasource:
            try:
                bands = [int(b) for b in datasource[GDAL_BANDS_ATTR]]
                data = data[:, :, bands]
            except Exception as ex:
                raise GdalLoaderError(f"Error using {GDAL_BANDS_ATTR}: {ex}")
        griddata.append(data)

    if len(griddata) == 0:
        raise GdalLoaderError("No GDAL grid source specified")
    elif len(griddata) == 1:
        data = np.vstack(griddata)

    # The YAML Reader expects axes in order j,i,p so shift parameter axis
    # tothe back
    data = np.moveaxis(data, 0, -1)

    logger.debug(f"GdalLoader: Loaded {gdalsource}")
    logger.debug(f"GdalLoader: size {gridsize}")
    logger.debug(f"GdalLoader: affine coeffs {gridaffine}")
    logger.debug(f"GdalLoader: Grid loaded with shape {data.shape}")
    return (data, gridsize, gridaffine)
