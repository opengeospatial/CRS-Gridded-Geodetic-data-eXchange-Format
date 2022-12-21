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

YAML_OPTION_GRID_DIRECTORY = "grid-directory"
YAML_OPTION_CHECK_DATASOURCE_AFFINE = "check-datasource-affine-coeffs"
YAML_OPTION_WRITE_HEADERS_ONLY = "write-headers-only"
YAML_OPTION_WRITE_CSV_GRIDS = "write-csv-grids"
YAML_OPTION_WRITE_CSV_COORDS = "write-csv-node-coordinates"

# Option for testing yaml headers without requiring valid grid data
YAML_OPTION_CREATE_DUMMY_GRID_DATA = "create-dummy-grid-data"

YAML_AFFINE_COEFF_DIFFERENCE_TOLERANCE = 1.0e-6

YAML_OPTION_GRID_DTYPE = "grid_dtype"
YAML_DTYPE_FLOAT32 = "float32"
YAML_DTYPE_FLOAT64 = "float64"

YAML_MAX_SIMPLE_STRING_LEN = 64
YAML_STR_TAG = "tag:yaml.org,2002:str"
YAML_MAP_TAG = "tag:yaml.org,2002:map"
YAML_SEQ_TAG = "tag:yaml.org,2002:seq"


YAML_READ_OPTIONS = f"""
  "{YAML_OPTION_GRID_DIRECTORY}" Base directory (relative to YAML file) used for grid files
  "{YAML_OPTION_CHECK_DATASOURCE_AFFINE}" Compare affine coeffs from data source with those defined in YAML (true or false)
  """

YAML_WRITE_OPTIONS = f"""
  "{YAML_OPTION_GRID_DIRECTORY}" Base directory (relative to YAML file) used for grid files
  "{YAML_OPTION_WRITE_CSV_GRIDS}" Write grids to external ggxf-csv grids (true or false, default true)
  "{YAML_OPTION_WRITE_CSV_COORDS}" Write node coordinates in CSV (true or false, default true)
  "{YAML_OPTION_WRITE_HEADERS_ONLY}" Write headers only - omit the grid data
"""

CSV_COORDINATE_FORMAT = ".12g"
CSV_PARAMETER_FORMAT = ".12g"

SOURCE_ATTR_SOURCE_TYPE = "dataSourceType"
SOURCE_ATTR_GRID_FILENAME = "gridFilename"
SOURCE_TYPE_GGXF_CSV = "ggxf-csv"

# Custom extensions for external data source
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
            group.configureParameters(self.error)
            for ygrid in ygrids:
                self.loadGrid(group, ygrid)
            group.configure(self.error)
            ggxf.addGroup(group)

    def installDummyGrid(self, group: Group, ygrid: dict):
        nparam = group.nparam()
        ni = ygrid.get(GRID_ATTR_I_NODE_COUNT, 1)
        nj = ygrid.get(GRID_ATTR_J_NODE_COUNT, 1)
        if GRID_ATTR_DATA_SOURCE in ygrid:
            ygrid.pop(GRID_ATTR_DATA_SOURCE)
        ygrid[GRID_ATTR_DATA] = np.zeros((nj, ni, nparam))

    def loadGrid(self, group: Group, ygrid: dict, parent: Grid = None):
        gridname = ygrid.get(GRID_ATTR_GRID_NAME, "unnamed")
        context = f"Grid {gridname}"
        ygrid = ygrid.copy()

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
            gdata = np.swapaxes(gdata, 0, 1)
            data = self.splitGridByParamSet(group, gdata)
            grid = Grid(group, gridname, ygrid, data)
            for cgrid in cgrids:
                self.loadGrid(group, cgrid, grid)
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
            datasourceModule = datasourceType.replace("-", "_")
            loader = importlib.import_module(
                f"..GridLoader.{datasourceModule}", __name__
            )
        except Exception as ex:
            self.error(
                f"Grid {gridname}: Cannot install loader for datatype {datasourceType}: {ex}"
            )
            return

        # Try the external grid loader.  This should return
        #   gridData - numpy array of the loaded data.  Maybe a full grid or a row-major reduction of
        #        if (eg [ni.nj,nparam])
        #   inferredSize - The grid size (ni,nj) if it can be inferred from the data source
        #   inferredAffine - The affine transformation coeffs if they can be inferred from the data source
        try:
            gridData, inferredSize, inferredAffine = loader.LoadGrid(
                group, datasource, self._logger
            )
        except Exception as ex:
            self.error(f"Grid {gridname}: Failed to load - {ex}")
            return

        # Allow extension to GGXF to infer grid size if not explicitly provided
        for axis, attr in enumerate((GRID_ATTR_I_NODE_COUNT, GRID_ATTR_J_NODE_COUNT)):
            if attr in ygrid:
                if inferredSize is not None and ygrid[attr] != inferredSize[axis]:
                    self.error(
                        f"Grid {gridname}: {attr} {ygrid[attr]} differs from {inferredSize[axis]} in {datasource}"
                    )
            elif inferredSize[axis]:
                ygrid[attr] = inferredSize[axis]
            else:
                self.error(
                    f"Grid {gridname}: {attr} is not defined and not inferrable from data source"
                )

        # Allow extension to GGXF to infer affine transformation if not explicitly provided
        if GRID_ATTR_AFFINE_COEFFS in ygrid:
            if inferredAffine is not None:
                affine = [float(c) for c in ygrid[GRID_ATTR_AFFINE_COEFFS]]
                diff = np.array(affine) - inferredAffine
                maxdiff = np.max(np.abs(diff))
                if maxdiff > YAML_AFFINE_COEFF_DIFFERENCE_TOLERANCE:
                    gtest = self.getBoolOption(
                        YAML_OPTION_CHECK_DATASOURCE_AFFINE, False
                    )
                    if gtest:
                        self.error(
                            f"{gridname} affine coefficients from dataSource don't match: {inferredAffine}"
                        )
                    else:
                        self._logger.warning(
                            f"{gridname} affine coefficients from dataSource {inferredAffine} differ from grid definition {affine} (max diff {maxdiff})"
                        )
        elif inferredAffine is not None:
            ygrid[GRID_ATTR_AFFINE_COEFFS] = inferredAffine
        else:
            self.error(
                f"Grid {gridname}: {GRID_ATTR_AFFINE_COEFFS} not defined and not inferrable from data source"
            )

        ygrid[GRID_ATTR_DATA] = gridData

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
        ni = ygrid.get(GRID_ATTR_I_NODE_COUNT)
        nj = ygrid.get(GRID_ATTR_J_NODE_COUNT)
        if not isinstance(data, np.ndarray):
            try:
                data = np.array(data)
            except:
                self.error(f"Failed to load grid {gridname} data into an array")
                return
            dtype = data.dtype
            if dtype == np.dtype("object"):
                self.error(
                    f"Failed to load grid {gridname} - bracketing may be inconsistent"
                )
            if not (
                np.issubdtype(dtype, np.integer) or np.issubdtype(dtype, np.floating)
            ):
                self.error(f"Failed to load grid {gridname} - not numeric data")
                return

        size = data.size
        shape = data.shape
        expectedSize = ni * nj * nparam
        # YAML grid order expects row, column, param corresponding to nj,ni,nparam
        expectedShape = (nj, ni, nparam)

        gridok = True
        if size != expectedSize:
            gridok = False
            self.error(
                f"Grid {gridname}: size {size} different to expected {expectedSize}"
            )
        # Valid option for number of dimensions
        if gridok and len(shape) > len(expectedShape):
            gridok = False
            self.error(
                f"Grid {gridname}: more dimensions ({len(shape)}) than expected ({len(expectedShape)})"
            )
        if gridok and shape != expectedShape:
            # Is the grid transposed?
            if (
                gridok
                and shape[0] != expectedShape[0]
                and shape[0] == expectedShape[1]
                and shape[1] == expectedShape[0]
            ):
                gridok = False
                self.error(f"Grid {gridname}: grid dimension wrong - likely transposed")
            # Check for flattening options of source grid.  This works because we already know the size is correct
            if gridok:
                shp = [*shape]
                eshp = [*expectedShape]
                while len(shp) > 0 and len(eshp) > 0:
                    if shp[0] == eshp[0]:
                        shp.pop(0)
                        eshp.pop(0)
                    elif shp[0] > eshp[0]:
                        e0 = eshp.pop(0)
                        eshp[0] *= e0
                    else:
                        gridok = False
                        self.error(
                            f"Grid {gridname}: YAML dimensions ({shape}) don't match expected {(expectedShape)} (nj,ni,np)"
                        )
            # Grid shape is compatible, so can reshape the grid to match.  Relies on numpy using row major ordering
            # internally for reshape.

            if gridok:
                data = data.reshape(expectedShape)
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
        # Placeholder for representing data in sets rather than single grid.
        # Future possibility to better align internal grid structure with NetCDF/binary structure
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
        dumper = yaml.SafeDumper
        dumper.add_representer(GGXF, self._writeGgxfHeader)
        dumper.add_representer(Group, self._writeGgxfGroup)
        dumper.add_representer(Grid, self._writeGgxfGrid)
        dumper.add_representer(np.ndarray, self._writeGridData)
        dumper.add_representer(str, self._writeStr)
        self._headerOnly = self.getBoolOption(YAML_OPTION_WRITE_HEADERS_ONLY, False)
        self._csvGrids = self.getBoolOption(YAML_OPTION_WRITE_CSV_GRIDS, True)
        self._csvCoords = self.getBoolOption(YAML_OPTION_WRITE_CSV_COORDS, True)
        self._csvFileTemplate = os.path.splitext(yaml_file)[0] + "-{csvid}.csv"
        self._csvFileGridNames = {}
        self._crdFormat = f"{{:{CSV_COORDINATE_FORMAT}}}".format
        self._prmFormat = f"{{:{CSV_PARAMETER_FORMAT}}}".format
        self._yamlFileDir = os.path.dirname(yaml_file)
        filename = os.path.basename(yaml_file)
        ggxf.setFilename(filename)

        with open(yaml_file, "w") as yamlh:
            yaml.safe_dump(ggxf, yamlh, indent=2, sort_keys=False)

    def _writeGgxfHeader(self, dumper, ggxf):
        ydata = ggxf.metadata().copy()
        ydata[GGXF_ATTR_GGXF_GROUPS] = ggxf._groups
        return dumper.represent_mapping(YAML_MAP_TAG, ydata)

    def _writeGgxfGroup(self, dumper, group):
        ydata = {GROUP_ATTR_GGXF_GROUP_NAME: group.name()}
        ydata.update(group.metadata())
        ydata[GROUP_ATTR_GRIDS] = group.grids()
        return dumper.represent_mapping(YAML_MAP_TAG, ydata)

    def _writeGgxfGrid(self, dumper, grid):
        ydata = {GRID_ATTR_GRID_NAME: grid.name()}
        ydata.update(grid.metadata())
        # Convert to numpy array so that they get picked up by representer with [] style of sequence.
        ydata[GRID_ATTR_AFFINE_COEFFS] = np.array(ydata[GRID_ATTR_AFFINE_COEFFS])
        ydata.pop(GRID_ATTR_DATA, None)
        if not self._headerOnly:
            data = self._gridDataWithNoDataFlag(grid)
            if self._csvGrids:
                gridfile = self._writeCsvGrid(grid, data)
                ydata[GRID_ATTR_DATA_SOURCE] = {
                    SOURCE_ATTR_SOURCE_TYPE: SOURCE_TYPE_GGXF_CSV,
                    SOURCE_ATTR_GRID_FILENAME: gridfile,
                }
            else:
                ydata[GRID_ATTR_DATA] = data
        if len(grid.grids()) > 0:
            ydata[GRID_ATTR_CHILD_GRIDS] = grid.grids()
        return dumper.represent_mapping(YAML_MAP_TAG, ydata)

    def _writeCsvGrid(self, grid, data):
        # Construct a unique grid name
        name = grid.name()
        name = re.sub(r"\W", "", name)[:YAML_MAX_SIMPLE_STRING_LEN].lower()
        gridid = self._csvFileGridNames.get(name, 1)
        self._csvFileGridNames[name] = gridid + 1
        filename = self._csvFileTemplate.replace("{csvid}", f"{name}{gridid:02d}")

        nodeCoordParams = grid.group().ggxf().nodeCoordinateParameters()
        groupParams = grid.group().parameterNames()

        try:
            # Consider using numpy.savetxt in the future...
            with open(filename, "w") as csvh:
                csvw = csv.writer(csvh)
                header = (
                    grid.group().ggxf().nodeCoordinateParameters()
                    if self._csvCoords
                    else []
                )
                csvw.writerow((*header, *grid.group().parameterNames()))
                shape = data.shape
                crd = []
                for jnode in range(shape[1]):
                    for inode in range(shape[0]):
                        if self._csvCoords:
                            xy = grid.calcxy([inode, jnode])
                            crd = [self._crdFormat(c) for c in xy]
                        prm = [self._prmFormat(p) for p in data[inode, jnode]]
                        csvw.writerow([*crd, *prm])
        except Exception as ex:
            self._logger.error(f"Error saving CSV grid file {filename}: {ex}")

        gridfile = os.path.relpath(filename, self._yamlFileDir)
        return gridfile

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
        if len(shape) > 1:
            ydata = np.swapaxes(ydata, 0, 1)

        ydata = ydata.tolist()
        return dumper.represent_sequence(YAML_SEQ_TAG, ydata, flow_style=True)

    def _writeStr(self, dumper, data):
        if "\n" in data or '"' in data or len(data) > YAML_MAX_SIMPLE_STRING_LEN:
            # Discard trailing spaces as these are not supported in flow style and
            # not significant in this context
            style = "|" if "\n" in data else ">"
            data = re.sub("\s+\n", "\n", data, flags=re.S)
            return dumper.represent_scalar(YAML_STR_TAG, data, style=style)
        return dumper.represent_scalar(YAML_STR_TAG, data)
