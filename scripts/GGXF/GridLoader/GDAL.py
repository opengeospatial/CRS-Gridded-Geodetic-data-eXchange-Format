#!/usr/bin/python3

from osgeo import gdal
import numpy as np
import logging
from ..Constants import *

GDAL_SOURCE_ATTR = "gdalSource"


class GdalLoaderError(RuntimeError):
    pass


def LoadGrid(datasource, logger):
    if logger is None:
        logger = logging.getLogger()
    gdalsource = datasource.get(GDAL_SOURCE_ATTR)
    if gdalsource is None:
        raise GdalLoaderError(f"{GDAL_SOURCE_ATTR} attribute is missing")
    logger.debug(f"Loading GDAL data from {gdalsource}")
    dataset = gdal.Open(gdalsource)
    if not dataset:
        raise GdalLoaderError(f"Failed to load GDAL data source {gdalsource}")
    tfm = dataset.GetGeoTransform()
    # NOTE: A lot of assumptions in this code about the relationship of the
    # GDAL GeoTransform and coordinate axes to the GGXF interpolation CRS.
    # Current implementation is based on
    affine = [
        float(c)
        for c in [
            tfm[3] + tfm[5] / 2.0,
            tfm[4],
            tfm[5],
            tfm[0] + tfm[1] / 2.0,
            tfm[1],
            tfm[2],
        ]
    ]

    size = (int(dataset.RasterXSize), int(dataset.RasterYSize))
    gridData = dataset.ReadAsArray()
    if len(gridData.shape) == 2:
        shape = (1, gridData.shape[0], gridData.shape[1])
        gridData = gridData.reshape(shape)
    gridData = np.moveaxis(gridData, 0, -1)
    logger.debug(f"GdalLoader: Loaded {gdalsource}")
    logger.debug(f"GdalLoader: size {size}")
    logger.debug(f"GdalLoader: affine coeffs {affine}")
    logger.debug(f"GdalLoader: Grid loaded with shape {gridData.shape}")
    return (size, affine, gridData)
