#!/usr/bin/python3

import csv
import json
import logging
import os.path
import re
import tempfile
import numpy as np

from .Constants import *
from .GGXF_Types import CommonAttributes, ContentTypes
from .TimeFunction import BaseTimeFunction, CompoundTimeFunction
from .AttributeValidator import AttributeValidator

JSON_METADATA_ATTR = "metadata"

PARAM_ATTRLIST_UNITNAME = [
    PARAM_ATTR_UNIT,
    PARAM_ATTR_LENGTH_UNIT,
    PARAM_ATTR_ANGLE_UNIT,
    PARAM_ATTR_SCALE_UNIT,
]


class Error(RuntimeError):
    pass


class GGXF:
    def __init__(self, metadata: dict, source: str = None, debug=False):
        self._metadata = metadata
        self._content = metadata[GGXF_ATTR_CONTENT]
        if self._content not in ContentTypes:
            raise Error("Invalid content type {self._content} for GGXF file")
        self._needEpoch = self._content in TimeDependentContentTypes
        self._groups = []
        self._configured = False
        self._parameters = None
        self._source = source
        self._debug = False
        self._logger = logging.getLogger("GGXF")
        self._valueat = lambda xy, epoch, refepoch: None
        if debug:
            self.setDebug()

    def setDebug(self, debug: bool = True):
        self._debug = debug
        self._logger.setLevel(logging.DEBUG if debug else logging.WARNING)

    def configure(self, errorhandler=None):
        parameters = {}
        if len(self._groups) == 1:
            self._valueat = self._groups[0].valueAt
        elif len(self._groups) > 1:
            self._valueat = self._sumValueAt

        for igroup, group in enumerate(self._groups):
            group.configure(errorhandler=errorhandler, id=f"{igroup}")
            for parameter in group.parameters():
                pname = parameter.name()
                if pname not in parameters:
                    parameters[pname] = parameter
                else:
                    ggxfparam = parameters[pname]
                    if parameter.unit() != ggxfparam.unit():
                        error = f"Inconsistent definition of parameter {pname} unit: {ggxfparam.unit()} and {parameter.unit()}"
                        if errorhandler:
                            errorhandler(error)
                        else:
                            raise Error(error)
                    if parameter.siratio() != ggxfparam.siratio():
                        error = f"Inconsistent definition of parameter {pname} unit: {ggxfparam.unit()} and {parameter.unit()}"
                        if errorhandler:
                            errorhandler(error)
                        else:
                            raise Error(error)
        self._parameters = list(parameters.values())
        # Configure mapping from group params to GGXF params
        paramIndex = {
            param.name(): iparam for iparam, param in enumerate(self._parameters)
        }
        self._groupParamMap = []
        for group in self.groups():
            parammap = [paramIndex[param.name()] for param in group.parameters()]
            self._groupParamMap.append(parammap)

        self._nullvalue = [None for p in self._parameters]
        # Cached values for groups to use in calculation at epoch
        self._calcEpoch = None
        self._calcGroups = list(self.groups())
        self._calcParamMap = self._groupParamMap
        self._zero = np.zeros((len(self._parameters),))
        self._configured = True

    def metadata(self):
        return self._metadata

    def contentType(self):
        return self._content

    def needEpoch(self):
        return self._needEpoch

    def logger(self):
        return self._logger

    def parameters(self):
        if not self._configured:
            self.configure()
        return self._parameters

    def addGroup(self, group):
        self._configured = False
        self._groups.append(group)

    def groups(self):
        for group in self._groups:
            yield group

    def allgrids(self):
        for group in self.groups():
            for grid in group.allgrids():
                yield grid

    def valueAt(self, xy, epoch=None, refepoch=None):
        if not self._configured:
            self.configure()
        if self._debug:
            self._logger.debug(f"Evaluating at {xy}, epochs {epoch} {refepoch}")
        if self._needEpoch:
            if epoch is None:
                raise Error(
                    f"Cannot evaluate {self._content} without providing an epoch"
                )
        return self._valueat(xy, epoch, refepoch)

    def _sumValueAt(self, xy, epoch=None, refepoch=None):
        # NOTE: this does not handle RMS summation of uncertainty at the moment :-(
        # NOTE: need to optimise away all of this for evaluating a single group
        if self._needEpoch:
            calcEpoch = (epoch, refepoch)
            if calcEpoch != self._calcEpoch:
                calcGroups = []
                calcParamMap = []
                for igroup, group in enumerate(self.groups()):
                    factor = group.timeFactorAt(epoch, refepoch)
                    if factor is not None and factor != 0.0:
                        calcGroups.append(group)
                        calcParamMap.append(self._groupParamMap[igroup])
                self._calcEpoch = calcEpoch
                self._calcGroups = calcGroups
                self._calcParamMap = calcParamMap
        if self._debug:
            self._logger.debug(
                f"Evaluating {len(self._calcGroups)} groups with non-zero time functions"
            )
        result = self._zero.copy()
        if len(self._calcGroups) == 0:
            return result
        for group, parammap in zip(self._calcGroups, self._calcParamMap):
            value = group.valueAt(xy, epoch, refepoch)
            if self._debug:
                self._logger.debug(f"{group.name()}: {value}:  {parammap}")
            if value is not None:
                result[parammap] += value
        return result

    def summary(self):
        metadata = self.metadata().copy()
        content = metadata.pop(GGXF_ATTR_CONTENT, "undefined")
        groups = [group.summary() for group in self.groups()]
        return {GGXF_ATTR_CONTENT: content, JSON_METADATA_ATTR: metadata, GGXF_ATTR_GGXF_GROUPS: groups}


class Group:
    def __init__(self, ggxf, groupname, metadata):
        self._ggxf = ggxf
        self._id = None
        self._name = groupname
        self._metadata = metadata
        parameters = [
            Parameter(paramdef) for paramdef in metadata.get(GROUP_ATTR_PARAMETERS, [])
        ]
        self._gridparameters = parameters
        self._parameters = parameters
        self._paramids = range(len(parameters))
        method = metadata.get(GROUP_ATTR_INTERPOLATION_METHOD)
        self._interpolator = GridInterpolator.getMethod(method)
        self._grids = []
        self._timeFunction = None
        funcdeflist = metadata.get(GROUP_ATTR_TIME_FUNCTIONS)
        if funcdeflist is not None:
            self._timeFunction = CompoundTimeFunction()
            for funcdef in funcdeflist:
                self._timeFunction.addFunction(BaseTimeFunction.Create(funcdef))
        self._configured = False
        self._needEpoch = ggxf.needEpoch()
        self._cacheEpoch = ()
        self._cacheFactor = None

    def name(self):
        return self._name

    def id(self):
        return self._id

    def metadata(self):
        return self._metadata

    def parameters(self):
        if not self._configured:
            raise Error("GGXF not configured")
        return self._parameters

    def nparam(self):
        return len(self._parameters)

    def grids(self):
        if not self._configured:
            raise Error("GGXF not configured")
        return self._grids

    def ggxf(self):
        return self._ggxf

    def logger(self):
        return self._ggxf.logger()

    def allgrids(self):
        for basegrid in self._grids:
            for grid in basegrid.allgrids():
                yield grid

    def addGrid(self, grid: "Grid"):
        self._grids.append(grid)
        self._configured = False

    def _configureParameters(self, errorhandler=None):
        ok = True
        contenttype = self._ggxf.contentType()
        contentdef = ContentTypes.get(contenttype)
        validparamsets = contentdef.get(ATTRDEF_PARAMETER_SETS, [])
        gridparams = [p.name() for p in self._gridparameters]
        paramids = None
        # Currently not supporting non GGXF parameters in a grid
        for paramset in validparamsets:
            if len(paramset) != len(gridparams):
                continue
            try:
                paramids = [gridparams.index(param) for param in paramset]
                break
            except ValueError:
                paramids = None
        if paramids is None:
            error = f"Invalid parameters ({','.join(gridparams)}) for content type {contenttype}"
            if errorhandler:
                errorhandler(error)
            else:
                raise Error(error)
            ok = False
        if ok:
            self._paramids = paramids
            self._parameters = [self._gridparameters[i] for i in self._paramids]
        return ok

    def _configureGrids(self, errorhandler=None):
        ok = True
        gindex = {grid.name(): grid for grid in self.allgrids()}
        shiftedGrids = []
        for grid in self._grids:
            pname = grid.get(GRID_ATTR_PARENT_GRID_NAME)
            if pname is not None:
                pgrid = gindex.get(pname)
                if pgrid is None:
                    ok = False
                    error = f"Parent grid {pname} of {grid.name()} not found"
                    if errorhandler:
                        errorhandler(error)
                    else:
                        raise Error(error)
                    continue
                shiftedGrids.append(grid)
                try:
                    pgrid.addGrid(grid)
                except Error as ex:
                    ok = False
                    if errorhandler:
                        errorhandler(str(ex))
                    else:
                        raise
        for grid in shiftedGrids:
            self._grids.remove(grid)
        for igrid, grid in enumerate(self._grids):
            if self._id:
                grid.setId(f"{self._id}:{igrid}")
        return ok

    def configure(self, id=None, errorhandler=None):
        if id:
            self._id = id
        ok = self._configureParameters(errorhandler)
        ok = ok and self._configureGrids(errorhandler)
        self._configured = ok

    def gridAt(self, xy):
        if not self._configured:
            raise Error("GGXF not configured")
        for grid in self.grids():
            if grid.contains(xy):
                cgrid = grid.gridAt(xy)
                if self._ggxf._debug:
                    self._ggxf._logger.debug(
                        f"{self._name}: grid at {xy}: {cgrid.id()} {cgrid.name()}"
                    )
                return cgrid
        return None

    def valueAt(self, xy, epoch=None, refepoch=None):
        if not self._configured:
            raise Error("GGXF not configured")
        grid = self.gridAt(xy)
        if grid is None:
            return None
        value = self._interpolator(grid, xy)
        value = value[self._paramids]
        if self._needEpoch:
            value *= self.timeFactorAt(epoch, refepoch)
        return value

    def timeFactorAt(self, epoch: float, refepoch: float = None):
        if not self._timeFunction:
            raise Error(f"Cannot evaluate {self.name()} - time function not defined")
        if epoch is None:
            raise Error(f"Cannot evaluate {self.name()} - epoch not defined")
        calcepoch = (epoch, refepoch)
        if calcepoch == self._cacheEpoch:
            return self._cacheFactor
        if refepoch is None:
            factor = self._timeFunction.valueAt(epoch)
        else:
            factor = self._timeFunction.valueChange(epoch, refepoch)
        self._cacheEpoch = calcepoch
        self._cacheFactor = factor
        return factor

    def summary(self):
        summary = self.metadata().copy()
        summary[GROUP_ATTR_PARAMETERS] = [param.name() for param in self.parameters()]
        summary[GROUP_ATTR_GRIDS] = [grid.summary() for grid in self.allgrids()]
        return summary


class Grid:
    """
    GGXF grid component

    Note: Grid data is held as a numpy array of shape (ncol,nrow,nparam], so indexing is j,i,p
    """

    def __init__(
        self, group: Group, gridname: str, metadata: dict, data: np.ndarray = None
    ):
        self._group = group
        self._id = None
        self._name = gridname
        self._metadata = dict(metadata)
        if GRID_ATTR_DATA in self._metadata:
            if data is not None:
                raise Error(f"Multiple definitions of data for grid {gridname}")
            data = self._metadata.pop(GRID_ATTR_DATA)

        self._subgrids = []
        self._parent = None
        coeffs = np.array(metadata[GRID_ATTR_AFFINE_COEFFS]).reshape((2, 3))
        self._xy0 = coeffs[:, 0]
        self._tfm = coeffs[:, 1:]
        self._inv = np.linalg.inv(self._tfm)
        self._imax = int(metadata[GRID_ATTR_I_NODE_COUNT] - 1)
        self._jmax = int(metadata[GRID_ATTR_J_NODE_COUNT] - 1)
        self._nparam = group.nparam()
        self._cellmax = np.array([self._imax - 1, self._jmax - 1])
        range = np.array(
            [
                self.calcxy([0.0, 0.0]),
                self.calcxy([0.0, self._jmax]),
                self.calcxy([self._imax, 0.0]),
                self.calcxy([self._imax, self._jmax]),
            ]
        )
        self._xmin, self._ymin = range.min(axis=0)
        self._xmax, self._ymax = range.max(axis=0)

        self._data = None
        if data is not None:
            self.setData(data)

    def id(self):
        return self._id

    def name(self) -> str:
        return self._name

    def metadata(self) -> dict:
        return self._metadata

    def parent(self):
        return self._parent

    def group(self):
        return self._group

    def logger(self):
        return self._group.logger()

    def data(self):
        return self._data

    def subgrids(self):
        return self._subgrids

    def extents(self):
        return [[self._xmin, self._ymin], [self._xmax, self._ymax]]

    def size(self):
        return (self._imax + 1, self._jmax + 1)

    def setId(self, id):
        self._id = id
        for igrid, subgrid in enumerate(self._subgrids):
            subgrid.setId(f"{id}:{igrid}")

    def addGrid(self, grid):
        if grid._group != self._group:
            raise Error(
                f'Grid nesting error: Grid "{self.name()}" cannot be parent of grid "{grid.name()}" in different group'
            )
        pname = grid.get(GRID_ATTR_PARENT_GRID_NAME)
        if pname is not None and pname != self._name:
            raise Error(
                f"Grid {grid.name()} parentName attribute conflicts with structural parent {self._name}"
            )
        pgrid = self
        while pgrid is not None:
            if pgrid == grid:
                raise Error(
                    f'Grid nesting error: Grid "{self.name()}" cannot be parent of its parent grid "{grid.name()}"'
                )
            pgrid = pgrid._parent
        gextents = grid.extents()
        if not self.contains(gextents[0]) or not self.contains(gextents[1]):
            self.logger().warn(
                f"Grid {grid.name()} is not fully contained in parent {self.name()}"
            )
        grid._parent = self
        self._subgrids.append(grid)

    def setData(self, data):
        data = np.array(data)
        shape = (self._jmax + 1, self._imax + 1, self._nparam)
        if data.shape == shape[:2]:
            data = data.reshape(shape)
        elif data.shape != shape:
            raise Error(
                f"Grid {self.name()} data dimensions {data.shape} don't match expected {shape}"
            )
        self._data = data

    def get(self, key: str):
        return self._metadata.get(key)

    def calcxy(self, ij):
        return self._xy0 + self._tfm.dot(ij)

    def calcij(self, xy):
        return self._inv.dot(xy - self._xy0)

    def contains(self, xy):
        return (
            xy[0] >= self._xmin
            and xy[0] <= self._xmax
            and xy[1] >= self._ymin
            and xy[1] <= self._ymax
        )

    def maxij(self):
        return self._imax, self._jmax

    def cellij(self, xy):
        rij = self.calcij(xy)
        cij = np.maximum([0, 0], np.minimum(self._cellmax, np.floor(rij).astype(int)))
        cxy = rij - cij
        return cij, cxy

    def gridAt(self, xy):
        if self.contains(xy):
            for g in self._subgrids:
                grid = g.gridAt(xy)
                if grid:
                    return grid
            return self
        return None

    def allgrids(self):
        yield self
        for subgrid in self._subgrids:
            for g in subgrid.allgrids():
                yield g

    def summary(self):
        "Returns a somewhat arbitrary summary of the grid contents"
        size = {"ngridi": self._imax + 1, "ngridj": self._jmax + 1}
        extents = {
            "xmin": float(self._xmin),
            "ymin": float(self._ymin),
            "xmax": float(self._xmax),
            "ymax": float(self._ymax),
        }
        params = [param.name() for param in self.group().parameters()]
        dtype = str(self._data.dtype)
        pmin = self._data.min(axis=(0, 1))
        pmax = self._data.max(axis=(0, 1))
        pdata = {
            parami: {"min": float(pmini), "max": float(pmaxi)}
            for parami, pmini, pmaxi in zip(params, pmin, pmax)
        }
        summary = {
            "name": self.name(),
            "size": size,
            "type": dtype,
            "extents": extents,
            "parameters": pdata,
        }
        if self.parent():
            summary["parent"] = self.parent().name()
        return summary


class GridInterpolator:
    # Note: Somewhat cryptic implementations using numpy arrays!
    # Note: Could be more efficiently implemented with numpy/scipy interpolation functions
    @staticmethod
    def bilinear(grid: Grid, xy):
        # Evaluate the value of parameters at a point from grid nodes using bilinear interpolation.
        # - determine which cell the point is in and the position cellxy of the point in the cell
        # (x,y coordinates ranging from 0 to 1)
        cellij, cellxy = grid.cellij(xy)
        data = grid.data()
        crnr = np.array([[0, 0], [0, 1], [1, 1], [1, 0]])
        # Determine the interpolation factors to multiply each node values by
        nodef = (
            (crnr[:, 0] * cellxy[0] + (1 - crnr[:, 0]) * (1 - cellxy[0]))
            * (crnr[:, 1] * cellxy[1] + (1 - crnr[:, 1]) * (1 - cellxy[1]))
        ).reshape((4, 1))
        # Get the node indices of the corner cells
        nodes = crnr + cellij
        # Multiply the values at the nodes by the interpolation factor
        nodeprm = data[nodes[:, 1], nodes[:, 0]]
        # Sum the scaled values to get the value at the evaluation point.
        val = (nodef * nodeprm).sum(axis=0)
        return val

    @staticmethod
    def biquadratic(grid: Grid, xy):
        # Evaluate the value of parameters at a point from grid nodes using biquadratic interpolation.
        # - determine which cell the point is in and the position cellxy of the point in the cell
        # (x,y coordinates ranging from 0 to 1)
        cellij, cellxy = grid.cellij(xy)
        gridsize = grid.size()
        data = grid.data()
        if gridsize[0] < 3 or gridsize[1] < 3:
            raise Error(
                f"Grid {grid.name()} not big enough for biquadratic interpolation"
            )
        if (cellxy[0] > 0.5 and cellij[0] < gridsize[0] - 2) or cellij[0] == 0:
            cellxy[0] -= 1.0
            cellij[0] += 1
        if (cellxy[1] > 0.5 and cellij[1] < gridsize[1] - 2) or cellij[1] == 0:
            cellxy[1] -= 1.0
            cellij[1] += 1
        cellxy = cellxy.reshape((2, 1))
        cellf = (
            (cellxy * cellxy).dot([[0.5, -1.0, 0.5]])
            + cellxy.dot([[-0.5, 0, 0.5]])
            + [0.0, 1.0, 0.0]
        )
        nodef = cellf[:1, :].T.dot(cellf[1:, :]).reshape((9, 1))
        crnr = np.array(
            [
                [-1, -1],
                [-1, 0],
                [-1, 1],
                [0, -1],
                [0, 0],
                [0, 1],
                [1, -1],
                [1, 0],
                [1, 1],
            ]
        )
        nodes = crnr + cellij
        # Multiply the values at the nodes by the interpolation factor
        nodeprm = data[nodes[:, 1], nodes[:, 0]]
        # Sum the scaled values to get the value at the evaluation point.
        val = (nodef * nodeprm).sum(axis=0)
        return val

    @staticmethod
    def bicubic(grid: Grid, xy):
        # Evaluate the value of parameters at a point from grid nodes using biquadratic interpolation.
        # - determine which cell the point is in and the position cellxy of the point in the cell
        # (x,y coordinates ranging from 0 to 1)
        cellij, cellxy = grid.cellij(xy)
        gridsize = grid.size()
        data = grid.data()
        if gridsize[0] < 4 or gridsize[1] < 4:
            raise Error(f"Grid {grid.name()} not big enough for bicubic interpolation")
        if cellij[0] == 0:
            cellxy[0] -= 1.0
            cellij[0] += 1
        elif cellij[0] >= gridsize[0] - 2:
            cellxy[0] += 1.0
            cellij[0] -= 1
        if cellij[1] == 0:
            cellxy[1] -= 1.0
            cellij[1] += 1
        elif cellij[1] >= gridsize[1] - 2:
            cellxy[1] += 1.0
            cellij[1] -= 1
        cellxy = cellxy.reshape((2, 1))
        cellf = (
            (cellxy * cellxy * cellxy).dot([[-1.0 / 6.0, 0.5, -0.5, 1.0 / 6.0]])
            + (cellxy * cellxy).dot([[0.5, -1.0, 0.5, 0.0]])
            + cellxy.dot([[-1.0 / 3.0, -0.5, 1.0, -1.0 / 6.0]])
            + [0.0, 1.0, 0.0, 0.0]
        )
        nodef = cellf[:1, :].T.dot(cellf[1:, :]).reshape(16, 1)
        crnr = np.array(
            [
                [-1, -1],
                [-1, 0],
                [-1, 1],
                [-1, 2],
                [0, -1],
                [0, 0],
                [0, 1],
                [0, 2],
                [1, -1],
                [1, 0],
                [1, 1],
                [1, 2],
                [2, -1],
                [2, 0],
                [2, 1],
                [2, 2],
            ]
        )
        nodes = crnr + cellij
        # Multiply the values at the nodes by the interpolation factor
        nodeprm = data[nodes[:, 1], nodes[:, 0]]
        # Sum the scaled values to get the value at the evaluation point.
        val = (nodef * nodeprm).sum(axis=0)
        return val

    Methods = {
        INTERPOLATION_METHOD_BILINEAR: bilinear.__func__,
        INTERPOLATION_METHOD_BIQUADRATIC: biquadratic.__func__,
        INTERPOLATION_METHOD_BICUBIC: bicubic.__func__,
    }

    def getMethod(methodName):
        if methodName not in GridInterpolator.Methods:
            raise Error(
                f"{GROUP_ATTR_INTERPOLATION_METHOD} {methodName} is not supported"
            )
        return GridInterpolator.Methods[methodName]


class Parameter:
    def __init__(self, metadata: dict):
        self._metadata = metadata
        self._name = metadata[PARAM_ATTR_PARAMETER_NAME]
        self._siratio = float(metadata.get(PARAM_ATTR_UNIT_SI_RATIO, 1.0))
        self._unit = "unspecified"
        for key, value in metadata.items():
            if key in PARAM_ATTRLIST_UNITNAME:
                self._unit = value
                break

    def name(self):
        return self._name

    def unit(self):
        return self._unit

    def siratio(self):
        return self._siratio


class BaseReader:
    def __init__(self, options=None):
        self._options = options or {}
        self._source = None
        self._loadok = True
        self._errors = []
        self._validator = AttributeValidator(CommonAttributes, errorhandler=self)
        self._logger = logging.getLogger("GGXF.BaseReader")

    def setSource(self, source):
        self._source = source
        self._loadok = True
        self._errors = []

    def validator(self):
        return self._validator

    def getOption(self, option, default=None):
        return self._options.get(option, default)

    def getBoolOption(self, option, default: bool = None) -> bool:
        value = self.getOption(option)
        if value == None:
            return default
        if type(value) == str:
            if (
                "true".startswith(value.lower())
                or "yes".startswith(value.lower())
                or value == "1"
            ):
                return True
            if (
                "false".startswith(value.lower())
                or "now".startswith(value.lower())
                or value == "0"
            ):
                return False
        return bool(value)

    def error(self, message):
        self._logger.error(message)
        self._errors.append(message)
        self._loadok = False

    def warn(self, message):
        self._logger.warn(message)

    def read(self):
        raise NotImplementedError(
            f"{type(self).__name__} read function not implemented"
        )


class BaseWriter:
    def __init__(self, options: dict = None):
        self._options = options or {}
        self._logger = logging.getLogger("GGXF.BaseWriter")

    def getOption(self, option, default=None):
        return self._options.get(option, default)

    def getBoolOption(self, option, default: bool = None) -> bool:
        value = self.getOption(option)
        if value == None:
            return default
        if type(value) == str:
            if (
                "true".startswith(value.lower())
                or "yes".startswith(value.lower())
                or value == "1"
            ):
                return True
            if (
                "false".startswith(value.lower())
                or "now".startswith(value.lower())
                or value == "0"
            ):
                return False
        return bool(value)

    def write(self):
        raise NotImplementedError(
            f"{type(self).__name__} write function not implemented"
        )
