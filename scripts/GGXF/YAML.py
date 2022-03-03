#!/usr/bin/python3
#
# YAML reader/writer for GGXF.
#
# YAML grid data in column major order corresponding to ncol,nrow,nparam numpy array.

import logging
import os.path
import re
import tempfile
import yaml
import numpy as np

from .GGXF import *
from . import GGXF_Types

YAML_OPTION_GRID_DIRECTORY = "grid_directory"
YAML_OPTION_CHECK_DATASOURCE_AFFINE = "check_datasource_affine_coeffs"
YAML_OPTION_USE_NESTED_GRIDS = "use_nested_grids"
YAML_OPTION_USE_GRIDDATA_SECTION = "use_griddata_section"
YAML_OPTION_WRITE_HEADERS_ONLY = "write_headers_only"
YAML_AFFINE_COEFF_DIFFERENCE_TOLERANCE = 1.0e-6

YAML_OPTION_GRID_DTYPE = "grid_dtype"
YAML_DTYPE_FLOAT32 = "float32"
YAML_DTYPE_FLOAT64 = "float64"

# Yaml writer creates these tags then cleanses the YAML to remove them
YAML_GGXF_TAG = "!ggxf"
YAML_GROUP_TAG = "!ggxfgroup"
YAML_GRID_TAG = "!ggxfgrid"
YAML_GRID_DATA_TAG = "!ggxfgriddata"

YAML_OPTIONS = f"""
The following options can apply to YAML format input (I) and output (O):

  "{YAML_OPTION_GRID_DIRECTORY}" (I) Base directory used for external grid source names
  "{YAML_OPTION_CHECK_DATASOURCE_AFFINE}" (I) Compare affine coeffs from data source with those defined in YAML (true or false)
  "{YAML_OPTION_USE_NESTED_GRIDS}" (O) Create nested grids in the output YAML (true or false, default true)
  "{YAML_OPTION_USE_GRIDDATA_SECTION}" (O) Use a gridData section for grid data (true or false, default true if more than one grid)
  "{YAML_OPTION_WRITE_HEADERS_ONLY} (O) Write headers only - omit the grid data"
"""


class Reader(BaseReader):
    @staticmethod
    def Read(yaml_file: str, options: dict = None) -> GGXF:
        if not os.path.exists(yaml_file):
            raise Error(f"GGXF YAML file {yaml_file} does not exist")
        reader = Reader(options)
        ggxf = reader.read(yaml_file)
        return ggxf

    def __init__(self, options=None):
        BaseReader.__init__(self, options)
        dtype = self.getOption(YAML_OPTION_GRID_DTYPE, YAML_DTYPE_FLOAT32)
        self._dtype = dtype = np.float64 if dtype == YAML_DTYPE_FLOAT64 else np.float32
        self._logger = logging.getLogger("GGXF.YamlReader")
        self.validator().update(GGXF_Types.YamlAttributes)

    def read(self, yaml_file):
        self._logger.debug(f"Loading YAML file {yaml_file}")
        self.setSource(yaml_file)
        try:
            if not os.path.isfile(yaml_file):
                raise Error(f"{yaml_file} does not exist or is not a file")
            try:
                ydata = yaml.load(open(yaml_file).read(), Loader=yaml.SafeLoader)
            except Exception as ex:
                raise Error(f"Cannot parse YAML in {yaml_file}: {ex}")
            if not isinstance(ydata, dict):
                raise Error(f"GGXF YAML file {yaml_file} doesn't hold a dictionary")

            if not self.validator().validateRootAttributes(ydata, context="GGXF"):
                raise Error(
                    f"GGXF YAML file {yaml_file} missing expected metadata fields"
                )
            self.loadGridData(ydata)
            ygroups = ydata.pop(GGXF_ATTR_GGXF_GROUPS, [])
            ggxf = GGXF(ydata)
            for ygroup in ygroups:
                self.loadGroup(ggxf, ygroup)
            ggxf.configure(self.error)
            if not self._loadok:
                ggxf = None
            return ggxf

        except Exception as ex:
            self._logger.error(f"Failed to load GGXF file {yaml_file}: {ex}")
            ggxf = None
        return ggxf

    def loadGroup(self, ggxf: GGXF, ygroup: dict):
        context = f"Group {ygroup.get(GROUP_ATTR_GGXF_GROUP_NAME,'unnamed')}"
        if self.validator().validateGroupAttributes(ygroup, context=context):
            groupname = ygroup.pop(GROUP_ATTR_GGXF_GROUP_NAME, None)
            ygrids = ygroup.pop(GROUP_ATTR_GRIDS, [])
            # Need to handle parameter validation here
            group = Group(ggxf, groupname, ygroup)
            for ygrid in ygrids:
                self.loadGrid(group, ygrid)
            group.configure(self.error)
            ggxf.addGroup(group)

    def loadGrid(self, group: Group, ygrid: dict, parent: Grid = None):
        context = f"Grid {ygrid.get(GRID_ATTR_GRID_NAME,'unnamed')}"
        if self.validator().validateGridAttributes(ygrid, context=context):
            data = ygrid.pop(GRID_ATTR_DATA, [])
            cgrids = ygrid.pop(GRID_ATTR_GRIDS, [])
            gridname = ygrid.pop(GRID_ATTR_GRID_NAME)
            # Lost validation of affine coefficients 6 numeric
            grid = Grid(group, gridname, ygrid, data)
            for cgrid in cgrids:
                self.loadGrid(group, cgrid, grid)
            if parent:
                parent.addGrid(grid)
            else:
                group.addGrid(grid)

    def loadGridData(self, ydata: dict):
        # Build a list of grids
        gridindex = {}
        gridnparam = {}
        for igroup, ygroup in enumerate(ydata.get(GGXF_ATTR_GGXF_GROUPS, [])):
            groupname = ygroup.get(GROUP_ATTR_GGXF_GROUP_NAME, f"{igroup+1}")
            params = ygroup.get(GROUP_ATTR_PARAMETERS, [])
            nparam = len(params)
            if not nparam:
                self.error(f"Group {groupname} header does not define any parameters")
            ygrids = ygroup.get(GROUP_ATTR_GRIDS, [])
            if type(ygrids) != list or len(ygrids) == 0:
                self.error(f"Group {groupname} does not define any grids")
                continue
            igrid = 0
            gridlist = []
            gridlist.extend(reversed(ygrids))
            while len(gridlist) > 0:
                ygrid = gridlist.pop()
                igrid += 1
                gridname = ygrid.get(GRID_ATTR_GRID_NAME)
                if type(gridname) != str or not gridname:
                    self.error(f"{gridname} does not have a name defined")
                    gridname = f"Group {groupname} grid {igrid+1}"
                if gridname in gridindex:
                    self.error(f"Grid name {gridname} is duplicated")
                else:
                    gridindex[gridname] = ygrid
                    gridnparam[gridname] = nparam
                if GRID_ATTR_GRIDS in ygrid:
                    subgrids = ygrid.get(GRID_ATTR_GRIDS)
                    if type(subgrids) != list:
                        self.error(
                            f"Grid {gridname} {GRID_ATTR_GRIDS} attribute is not a list"
                        )
                    else:
                        gridlist.extend(reversed(subgrids))

        # Copy information from the gridData section if it is defined
        griddatasets = ydata.pop(GGXF_ATTR_GRID_DATA, None)
        if griddatasets is not None:
            for igriddata, griddata in enumerate(griddatasets):
                gridname = griddata.get(GRID_ATTR_GRID_NAME)
                if gridname not in gridindex:
                    self.error(
                        f"{GGXF_ATTR_GRID_DATA} grid {gridname} is not defined in any of the groups"
                    )
                    continue
                ygrid = gridindex.get(gridname)
                for key in griddata:
                    if key != GRID_ATTR_GRID_NAME and key in ygrid:
                        self.error(
                            f"{key} is defined in both {GGXF_ATTR_GRID_DATA} and in the group grid"
                        )
                    else:
                        ygrid[key] = griddata[key]

        # Now install the grid data - this need to be converted to a numpy array
        # If the options define a grid directory then change directory to that before
        # trying to load the grids.

        startdir = os.getcwd()
        griddir = self.getOption(YAML_OPTION_GRID_DIRECTORY, startdir)
        dirset = False
        try:
            for gridname, ygrid in gridindex.items():
                nparam = gridnparam[gridname]
                source_data = {}
                source_nparam = None
                if GRID_ATTR_DATA_SOURCE in ygrid:
                    if GRID_ATTR_DATA in ygrid:
                        self.error(
                            f"Grid {gridname} has {GRID_ATTR_DATA_SOURCE} and {GRID_ATTR_DATA}"
                        )

                    datasource = ygrid.pop(GRID_ATTR_DATA_SOURCE)
                    if not dirset:
                        self._logger.debug(
                            f"Changing directory to {griddir} to load grids"
                        )
                        os.chdir(griddir)
                        dirset = True
                    self.loadGdalGrid(gridname, ygrid, datasource)
                elif nparam:
                    ncol = ygrid.get(GRID_ATTR_J_NODE_COUNT)
                    nrow = ygrid.get(GRID_ATTR_I_NODE_COUNT)
                    expectedSize = nparam * nrow * ncol
                    expectedShape = (ncol, nrow, nparam)
                    gridok = False
                    data = ygrid.get(GRID_ATTR_DATA)
                    if nrow and ncol and data:
                        try:
                            data = np.array(data)
                            shape = data.shape
                            gridok = True
                        except Exception as ex:
                            self.error(
                                f"Grid {gridname}: Could not read grid data: {ex}"
                            )
                    if gridok:
                        size = data.size
                        if size != expectedSize:
                            gridok = False
                            self.error(
                                f"Grid {gridname}: size {size} different to expected {expectedSize}"
                            )
                    if gridok:
                        if len(shape) == 1:
                            shape = expectedShape
                            data = data.reshape(shape)
                        elif len(shape) == 2:
                            shape = (shape[0], shape[1], 1)
                            data.reshape(shape)
                        elif len(shape) != 3:
                            gridok = False
                            self.error(
                                f"Grid {gridname} has the wrong number of dimensions {len(shape)}"
                            )
                    if gridok and shape != expectedShape:
                        gridok = False
                        self.error(
                            f"Grid {gridname}: dimensions {data.shape} does not match expected {expectedShape} - likely transposed grid"
                        )
                    if gridok:
                        if data.dtype != self._dtype:
                            data = data.astype(self._dtype)
                        ygrid[GRID_ATTR_DATA] = data
                        self._logger.debug(
                            f"Grid {gridname} loaded - dimensions {data.shape}, type {data.dtype}"
                        )
        finally:
            os.chdir(startdir)

    def loadGdalGrid(self, gridname, ygrid, datasource):
        # NOTE: This probably needs additional options for selecting bands,
        # order of interpolation coordinates, etc.
        from osgeo import gdal

        try:
            self._logger.debug(f"Loading GDAL data from {datasource}")
            dataset = gdal.Open(datasource)
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

            inodemax = dataset.RasterXSize - 1
            jnodemax = dataset.RasterYSize - 1
            gridData = dataset.ReadAsArray()
            if len(gridData.shape) == 2:
                shape = (1, gridData.shape[0], gridData.shape[1])
                gridData = gridData.reshape(shape)
            gridData = np.moveaxis(gridData, 0, -1)
            self._logger.debug(f"Loaded with dimensions {gridData.shape}")

            if GRID_ATTR_I_NODE_COUNT in ygrid:
                imax = ygrid[GRID_ATTR_I_NODE_COUNT] - 1
                if imax != inodemax:
                    self.error(
                        f"{gridname} {GRID_ATTR_I_NODE_COUNT} {imax} differs from {inodemax} in {datasource}"
                    )
            else:
                ygrid[GRID_ATTR_I_NODE_COUNT] = inodemax + 1

            if GRID_ATTR_J_NODE_COUNT in ygrid:
                imax = ygrid[GRID_ATTR_J_NODE_COUNT] - 1
                if imax != jnodemax:
                    self.error(
                        f"{gridname} {GRID_ATTR_J_NODE_COUNT} {imax} differs from {jnodemax} in {datasource}"
                    )
            else:
                ygrid[GRID_ATTR_J_NODE_COUNT] = jnodemax + 1

            if GRID_ATTR_AFFINE_COEFFS in ygrid:
                gaffine = [float(c) for c in ygrid[GRID_ATTR_AFFINE_COEFFS]]
                diff = np.array(gaffine) - affine
                maxdiff = np.max(np.abs(diff))
                if maxdiff > YAML_AFFINE_COEFF_DIFFERENCE_TOLERANCE:
                    gtest = self.getBoolOption(
                        YAML_OPTION_CHECK_DATASOURCE_AFFINE, False
                    )
                    if gtest:
                        self.error(
                            f"{gridname} affine coefficients from {datasource} don't match: {affine}"
                        )
                    else:
                        self._logger.warning(
                            f"{gridname} affine coefficients from {datasource} differ from grid definition (max diff {maxdiff})"
                        )
            else:
                ygrid[GRID_ATTR_AFFINE_COEFFS] = affine

            ygrid[GRID_ATTR_DATA] = gridData
        except Exception as ex:
            self.error(f"Grid {gridname}: Failed to load {datasource}: {ex}")


class Writer(BaseWriter):
    # PyYAML has an annoying trait of adding tags.  While it makes the YAML loader "safe"
    # it is not consistent with the GGXF YAML spec.  To get around this the YAML is first written
    # to a string, the tags are removed with a regular expression, and then the YAML is written to the
    # output file.  This may die for large GGXF files!
    #
    # Another option for YAML would be to write to JSON.

    @staticmethod
    def Write(ggxf, yaml_file, options=None):
        writer = Writer(options)
        writer.write(ggxf, yaml_file)

    def __init__(self, options=None):
        BaseWriter.__init__(self, options)
        self._logger = logging.getLogger("GGXF.YamlWriter")

    def write(self, ggxf, yaml_file):
        # Not sure about this code - changes the YAML module I think?
        loader = yaml.SafeDumper
        loader.add_representer(GGXF, self._writeGgxfHeader)
        loader.add_representer(Group, self._writeGgxfGroup)
        loader.add_representer(Grid, self._writeGgxfGrid)
        loader.add_representer(np.ndarray, self._writeGridData)
        self._useNestedGrids = self.getBoolOption(YAML_OPTION_USE_NESTED_GRIDS, True)
        self._headerOnly = self.getBoolOption(YAML_OPTION_WRITE_HEADERS_ONLY, False)

        with tempfile.TemporaryFile("w+") as tmph, open(yaml_file, "w") as yamlh:
            yaml.safe_dump(ggxf, tmph, indent=2, sort_keys=False)
            tmph.seek(0)
            tags = [
                re.escape(t)
                for t in (
                    YAML_GGXF_TAG,
                    YAML_GROUP_TAG,
                    YAML_GRID_TAG,
                    YAML_GRID_DATA_TAG,
                )
            ]
            tagpattern = r"(" + "|".join(tags) + r")\b *"
            tagre = re.compile(tagpattern)
            blank = re.compile(r"^\s*$")
            for line in tmph:
                line = tagre.sub("", line)
                if not blank.match(line):
                    yamlh.write(line)

    def _writeGgxfHeader(self, dumper, ggxf):
        ydata = ggxf.metadata().copy()
        ydata["groups"] = ggxf._groups
        allgrids = list(ggxf.allgrids())
        multipleGrids = len(allgrids) > 1
        self._useGridDataSection = self.getBoolOption(
            YAML_OPTION_USE_GRIDDATA_SECTION, multipleGrids
        )
        if self._useGridDataSection and not self._headerOnly:
            griddata = [
                {GRID_ATTR_GRID_NAME: grid.name(), GRID_ATTR_DATA: grid.data()}
                for grid in allgrids
            ]
            ydata[GGXF_ATTR_GRID_DATA] = griddata
        return dumper.represent_mapping(YAML_GGXF_TAG, ydata)

    def _writeGgxfGroup(self, dumper, group):
        ydata = group.metadata().copy()
        ydata[GROUP_ATTR_GGXF_GROUP_NAME] = group.name()
        if self._useNestedGrids:
            ydata["grids"] = group.grids()
        else:
            ydata["grids"] = list(group.allgrids())
        return dumper.represent_mapping(YAML_GROUP_TAG, ydata)

    def _writeGgxfGrid(self, dumper, grid):
        ydata = grid.metadata().copy()
        ydata[GRID_ATTR_AFFINE_COEFFS] = [
            float(c) for c in ydata[GRID_ATTR_AFFINE_COEFFS]
        ]
        ydata.pop(GRID_ATTR_PARENT_GRID_NAME, None)
        if not self._useNestedGrids and grid.parent() is not None:
            ydata[GRID_ATTR_PARENT_GRID_NAME] = grid.parent().name()
        elif len(grid.subgrids()) > 0:
            ydata["grids"] = grid.subgrids()
        ydata.pop(GRID_ATTR_DATA, None)
        if not self._useGridDataSection and not self._headerOnly:
            ydata[GRID_ATTR_DATA] = grid.data()
        return dumper.represent_mapping(YAML_GGXF_TAG, ydata)

    def _writeGridData(self, dumper, data):
        shape = data.shape
        ydata = data
        if len(shape) == 3 and shape[2] == 1:
            ydata = data.reshape(shape[:2])
        ydata = ydata.tolist()
        return dumper.represent_sequence(YAML_GRID_DATA_TAG, ydata)
