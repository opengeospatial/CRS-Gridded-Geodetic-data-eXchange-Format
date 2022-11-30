#!/usr/bin/python3
#
# YAML reader/writer for GGXF.
#
# YAML grid data in column major order corresponding to ncol,nrow,nparam numpy array.

import logging
import os.path
import re
import tempfile
import importlib
import yaml
import numpy as np

from .GGXF import *
from . import GGXF_Types

YAML_OPTION_GRID_DIRECTORY = "grid_directory"
YAML_OPTION_CHECK_DATASOURCE_AFFINE = "check_datasource_affine_coeffs"
YAML_OPTION_USE_GRIDDATA_SECTION = "use_griddata_section"
YAML_OPTION_WRITE_HEADERS_ONLY = "write_headers_only"
# Option for testing yaml headers without requiring valid grid data
YAML_OPTION_CREATE_DUMMY_GRID_DATA = "create_dummy_grid_data"
YAML_AFFINE_COEFF_DIFFERENCE_TOLERANCE = 1.0e-6

YAML_OPTION_GRID_DTYPE = "grid_dtype"
YAML_DTYPE_FLOAT32 = "float32"
YAML_DTYPE_FLOAT64 = "float64"

# Yaml writer creates these tags then cleanses the YAML to remove them
YAML_GGXF_TAG = "!ggxf"
YAML_GROUP_TAG = "!ggxfgroup"
YAML_GRID_TAG = "!ggxfgrid"
YAML_GRID_DATA_TAG = "!ggxfgriddata"


YAML_MAX_SIMPLE_STRING_LEN = 32
YAML_STR_SCALAR_TAG = "tag:yaml.org,2002:str"


YAML_OPTIONS = f"""
The following options can apply to YAML format input (I) and output (O):

  "{YAML_OPTION_GRID_DIRECTORY}" (I) Base directory used for external grid source names
  "{YAML_OPTION_CHECK_DATASOURCE_AFFINE}" (I) Compare affine coeffs from data source with those defined in YAML (true or false)
  "{YAML_OPTION_USE_GRIDDATA_SECTION}" (O) Use a gridData section for grid data (true or false, default true if more than one grid)
  "{YAML_OPTION_WRITE_HEADERS_ONLY}" (O) Write headers only - omit the grid data
"""

SOURCE_ATTR_SOURCE_TYPE = "sourceType"
# Common data source attributes allowing transformation of parameters
SOURCE_ATTR_PARAMETER_TRANSFORMATION = "parameterTransformations"
SOURCE_XFORM_ATTR_PARAMETER_NAME = "parameterName"
SOURCE_XFORM_ATTR_PARAMETER_SCALE = "scale"
SOURCE_XFORM_ATTR_PARAMETER_OFFSET = "offset"


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
        self._useDummyGridData = self.getBoolOption(
            YAML_OPTION_CREATE_DUMMY_GRID_DATA, False
        )
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
            gridDataSource = self.loadGridDataSection(ydata)
            ygroups = ydata.pop(GGXF_ATTR_GGXF_GROUPS, [])
            ggxf = GGXF(ydata)
            for ygroup in ygroups:
                self.loadGroup(ggxf, ygroup, gridDataSource)
            ggxf.configure(self.error)
            if not self._loadok:
                ggxf = None
            return ggxf

        except Exception as ex:
            self._logger.error(f"Failed to load GGXF file {yaml_file}: {ex}")
            ggxf = None
        return ggxf

    def loadGroup(self, ggxf: GGXF, ygroup: dict, gridDataSource: dict):
        context = f"Group {ygroup.get(GROUP_ATTR_GGXF_GROUP_NAME,'unnamed')}"
        if self.validator().validateGroupAttributes(ygroup, context=context):
            groupname = ygroup.pop(GROUP_ATTR_GGXF_GROUP_NAME, None)
            ygrids = ygroup.pop(GROUP_ATTR_GRIDS, [])
            # Need to handle parameter validation here
            group = Group(ggxf, groupname, ygroup)
            group.configureParameters(self.error)
            for ygrid in ygrids:
                self.loadGrid(group, ygrid, gridDataSource)
            group.configure(self.error)
            ggxf.addGroup(group)

    def loadGridDataSection(self, ydata: dict):
        gridDataSource = {}
        sources = ydata.get(GGXF_ATTR_GRID_DATA, [])
        for gdata in sources:
            griddata = gdata.copy()
            gridname = griddata.pop(GGXF_ATTR_GRID_NAME)
            gridDataSource[gridname] = griddata
        return gridDataSource

    def installDummyGrid(self, group: Group, ygrid: dict):
        nparam = group.nparam()
        ncol = ygrid.get(GRID_ATTR_J_NODE_COUNT, 1)
        nrow = ygrid.get(GRID_ATTR_I_NODE_COUNT, 1)
        if GRID_ATTR_DATA_SOURCE in ygrid:
            ygrid.pop(GRID_ATTR_DATA_SOURCE)
        ygrid[GRID_ATTR_DATA] = np.zeros((ncol, nrow, nparam))

    def loadGrid(
        self, group: Group, ygrid: dict, gridDataSource: dict, parent: Grid = None
    ):
        gridname = ygrid.get(GRID_ATTR_GRID_NAME, "unnamed")
        context = f"Grid {gridname}"
        ygrid = ygrid.copy()

        # Merge attributes from gridData section
        if gridname in gridDataSource:
            attr = gridDataSource.pop(gridname)
            for key, value in attr.items():
                if key in ygrid:
                    self.error(
                        f"{key} is defined in both {GGXF_ATTR_GRID_DATA} and in the group grid"
                    )
                ygrid[key] = value

        # Load grid data. This will amend the grid definition by adding the data element
        # and potentially the row and column count and the affine transformation
        #
        # Otherwise load the grid data into a numpy array

        if self._useDummyGridData:
            self.installDummyGrid(group, ygrid)

        if GRID_ATTR_DATA_SOURCE in ygrid and GRID_ATTR_DATA not in ygrid:
            datasource = ygrid.pop(GRID_ATTR_DATA_SOURCE)
            ygrid[GRID_ATTR_DATA] = None
            self.installGridFromSource(group, ygrid, datasource)
            if SOURCE_ATTR_PARAMETER_TRANSFORMATION in datasource:
                self.applyParameterTransformation(
                    group,
                    ygrid[GRID_ATTR_DATA],
                    datasource[SOURCE_ATTR_PARAMETER_TRANSFORMATION],
                )

        if self.validator().validateGridAttributes(ygrid, context=context):
            self.validateGridData(group, ygrid)
            gdata = ygrid.pop(GRID_ATTR_DATA, [])
            cgrids = ygrid.pop(GRID_ATTR_CHILD_GRIDS, [])
            gridname = ygrid.pop(GRID_ATTR_GRID_NAME)
            data = self.splitGridByParamSet(group, gdata)
            grid = Grid(group, gridname, ygrid, data)
            for cgrid in cgrids:
                self.loadGrid(group, cgrid, gridDataSource, grid)
            if parent:
                parent.addGrid(grid)
            else:
                group.addGrid(grid)

    def installGridFromSource(self, group: Group, ygrid: dict, datasource: dict):
        startdir = os.getcwd()
        griddir = self.getOption(YAML_OPTION_GRID_DIRECTORY, startdir)
        try:
            os.chdir(griddir)
            self.loadExternalGrid(group, ygrid, datasource)
        finally:
            os.chdir(startdir)

    def loadExternalGrid(self, group: Group, ygrid, datasource):
        # NOTE: This probably needs additional options for selecting bands,
        # order of interpolation coordinates, etc

        gridname = ygrid.get(GRID_ATTR_GRID_NAME, "unnamed")

        datasourceType = datasource.get(SOURCE_ATTR_SOURCE_TYPE)
        if datasourceType is None:
            self.error(
                f"Grid {gridname}: {GRID_ATTR_DATA_SOURCE} needs a {SOURCE_ATTR_SOURCE_TYPE} attribute"
            )
            return

        try:
            if not re.match(r"^[\w\-]+$", datasourceType):
                raise RuntimeError(f"Invalid {SOURCE_ATTR_SOURCE_TYPE}")
            loader = importlib.import_module(f"..GridLoader.{datasourceType}", __name__)
        except Exception as ex:
            self.error(
                f"Grid {gridname}: Cannot install loader for datatype {datasourceType}: {ex}"
            )
            return

        try:
            size, affine, gridData = loader.LoadGrid(group, datasource, self._logger)
        except Exception as ex:
            self.error(f"Grid {gridname}: Failed to load - {ex}")
            return
        if affine is None:
            affine = [float(c) for c in ygrid[GRID_ATTR_AFFINE_COEFFS]]
        if size is None:
            size = [
                ygrid[GRID_ATTR_I_NODE_COUNT],
                ygrid[GRID_ATTR_J_NODE_COUNT],
                group.nparam(),
            ]
            if gridData.size != size[0] * size[1] * size[2]:
                self.error((f"Grid {gridname} is the wrong size"))
                return
            # As size not set assume that grid dimensions are arbitrary, so set to
            # expected dimensions
            gridData = gridData.reshape((size[1], size[0], size[2]))

        try:
            if GRID_ATTR_I_NODE_COUNT in ygrid:
                if ygrid[GRID_ATTR_I_NODE_COUNT] != size[0]:
                    self.error(
                        f"{gridname} {GRID_ATTR_I_NODE_COUNT} {ygrid[GRID_ATTR_I_NODE_COUNT]} differs from {size[0]} in {datasource}"
                    )
            else:
                ygrid[GRID_ATTR_I_NODE_COUNT] = size[0]

            if GRID_ATTR_J_NODE_COUNT in ygrid:
                if ygrid[GRID_ATTR_J_NODE_COUNT] != size[1]:
                    self.error(
                        f"{gridname} {GRID_ATTR_J_NODE_COUNT} {ygrid[GRID_ATTR_J_NODE_COUNT]} differs from {size[1]} in {datasource}"
                    )
            else:
                ygrid[GRID_ATTR_J_NODE_COUNT] = size[1]

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
                            f"{gridname} affine coefficients from dataSource don't match: {affine}"
                        )
                    else:
                        self._logger.warning(
                            f"{gridname} affine coefficients from dataSource {affine} differ from grid definition {affine} (max diff {maxdiff})"
                        )
            else:
                ygrid[GRID_ATTR_AFFINE_COEFFS] = affine

            ygrid[GRID_ATTR_DATA] = gridData
        except Exception as ex:
            self.error(f"Grid {gridname}: Failed to load - {ex}")

    def applyParameterTransformation(self, group, grid, transforms):
        if not isinstance(transforms, list):
            self.error(
                f"{SOURCE_ATTR_PARAMETER_TRANSFORMATION} must contain a list of transformations"
            )
            return
        paramNames = list(group.parameterNames())
        for transform in transforms:
            try:
                name = transform.get(SOURCE_XFORM_ATTR_PARAMETER_NAME)
                if name not in paramNames:
                    raise RuntimeError(f"{name} is not a valid parameter name")
                nprm = paramNames.index(name)
                scale = float(transform.get(SOURCE_XFORM_ATTR_PARAMETER_SCALE, 1.0))
                offset = float(transform.get(SOURCE_XFORM_ATTR_PARAMETER_OFFSET, 0.0))
                grid[:, :, nprm] = grid[:, :, nprm] * scale + offset
            except Exception as ex:
                self.error(f"Error in {SOURCE_ATTR_PARAMETER_TRANSFORMATION}: {ex}")

    def validateGridData(self, group, ygrid):
        gridname = ygrid.get(GRID_ATTR_GRID_NAME, "unnamed")
        data = ygrid.get(GRID_ATTR_DATA)
        if data is None:
            return
        nparam = group.nparam()
        ncol = ygrid.get(GRID_ATTR_J_NODE_COUNT)
        nrow = ygrid.get(GRID_ATTR_I_NODE_COUNT)
        if not isinstance(data, np.ndarray):
            try:
                data = np.array(data)
            except:
                self.error("Failed to load grid {gridname} data into an array")
                return

        size = data.size
        shape = data.shape
        expectedSize = nparam * nrow * ncol
        expectedShape = (ncol, nrow, nparam)

        gridok = True
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
                data = data.reshape(shape)
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
            self._logger.debug(
                f"Grid {gridname} loaded - dimensions {data.shape}, type {data.dtype}"
            )
            # Mask the array if it contains missing values

            mask = None
            for iparam, param in enumerate(group.parameters()):
                noDataFlag = param.noDataFlag()
                if noDataFlag is not None:
                    if mask is None:
                        mask = np.zeros(data.shape, dtype=bool)
                    mask[:, :, iparam] = data[:, :, iparam] == noDataFlag

            if mask is not None:
                nmissing = np.count_nonzero(mask)
                self._logger.debug(
                    f"Grid {gridname} - masking {nmissing} missing values"
                )
                if nmissing > 0:
                    data = np.ma.masked_array(data, mask=mask)
            ygrid[GRID_ATTR_DATA] = data

    def splitGridByParamSet(self, group, gdata):
        # Placeholder for representing data in sets rather than single grid
        return gdata
        # paramSetIndices = group.paramSetIndices()
        # return {pset: gdata[:, :, indices] for pset, indices in paramSetIndices.items()}


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
        loader.add_representer(str, self._writeStr)
        self._headerOnly = self.getBoolOption(YAML_OPTION_WRITE_HEADERS_ONLY, False)
        filename = os.path.basename(yaml_file)
        ggxf.setFilename(filename)

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
        ydata[GGXF_ATTR_GGXF_GROUPS] = ggxf._groups
        allgrids = list(ggxf.allgrids())
        multipleGrids = len(allgrids) > 1
        self._useGridDataSection = self.getBoolOption(
            YAML_OPTION_USE_GRIDDATA_SECTION, multipleGrids
        )
        if self._useGridDataSection and not self._headerOnly:
            griddata = [
                {
                    GRID_ATTR_GRID_NAME: grid.name(),
                    GRID_ATTR_DATA: self._gridDataWithNoDataFlag(grid),
                }
                for grid in allgrids
            ]
            ydata[GGXF_ATTR_GRID_DATA] = griddata
        return dumper.represent_mapping(YAML_GGXF_TAG, ydata)

    def _writeGgxfGroup(self, dumper, group):
        ydata = group.metadata().copy()
        ydata[GROUP_ATTR_GGXF_GROUP_NAME] = group.name()
        ydata[GROUP_ATTR_GRIDS] = group.grids()
        return dumper.represent_mapping(YAML_GROUP_TAG, ydata)

    def _writeGgxfGrid(self, dumper, grid):
        ydata = grid.metadata().copy()
        ydata[GRID_ATTR_AFFINE_COEFFS] = [
            float(c) for c in ydata[GRID_ATTR_AFFINE_COEFFS]
        ]
        if len(grid.grids()) > 0:
            ydata[GRID_ATTR_CHILD_GRIDS] = grid.grids()
        ydata.pop(GRID_ATTR_DATA, None)
        if not self._useGridDataSection and not self._headerOnly:
            ydata[GRID_ATTR_DATA] = self._gridDataWithNoDataFlag(grid)
        return dumper.represent_mapping(YAML_GGXF_TAG, ydata)

    def _gridDataWithNoDataFlag(self, grid):
        data = grid.data()
        if isinstance(data, np.ma.core.MaskedArray):
            mask = data.mask
            ydata = data.data
            if np.count_nonzero(mask) == 0:
                data = ydata
            else:
                data = data.copy()
                for iparam, param in enumerate(grid.group().parameters()):
                    noDataFlag = param.noDataFlag()
                    if noDataFlag is not None:
                        pdata = data[:, :, iparam]
                        pdata[pdata.mask] = noDataFlag
                        data[:, :, iparam] = pdata
                    elif np.count_nonzero(data.mask[:, :, iparam]) > 0:
                        self._logger.error(
                            f"Error saving GGXF to YAML: noDataFlag not defined for {param.name()}"
                        )
            data = data.data
        return data

    def _writeGridData(self, dumper, data):
        shape = data.shape
        ydata = data
        if len(shape) == 3 and shape[2] == 1:
            ydata = data.reshape(shape[:2])

        ydata = ydata.tolist()
        return dumper.represent_sequence(YAML_GRID_DATA_TAG, ydata)

    # This attempts to improve the format of output YAML strings (eg WKT).  Hasn't
    # worked :-(
    def _writeStr(self, dumper, data):
        if "\n" in data or '"' in data or len(data) > YAML_MAX_SIMPLE_STRING_LEN:
            return dumper.represent_scalar(YAML_STR_SCALAR_TAG, data, style="literal")
        return dumper.represent_scalar(YAML_STR_SCALAR_TAG, data)
