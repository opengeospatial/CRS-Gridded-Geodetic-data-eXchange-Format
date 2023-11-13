#!/usr/bin/python3
from __future__ import annotations

import csv
import json
import logging
import os.path
import re
import tempfile

import numpy as np

from .AttributeValidator import AttributeValidator
from .Constants import *
from .GGXF_Types import CommonAttributes, ContentTypes
from .TimeFunction import BaseTimeFunction, CompoundTimeFunction

JSON_METADATA_ATTR = "metadata"

# Minimal mapping from CRSWKT direction to node coordinate. Mapping used
# is the first entry for which the key is contained in the CRS type (eg GEOGCRS)

NODE_COORDINATE_PARAMETERS = {
    "GEOG": {"east": "nodeLongitude", "north": "nodeLatitude"},
    "PROJ": {"east": "nodeEasting", "north": "nodeNorthing"},
}


class Error(RuntimeError):
    pass


class GGXF:
    def __init__(self, metadata: dict, source: str = None, debug=False):
        self._metadata = metadata
        self._content = metadata[GGXF_ATTR_CONTENT]
        if self._content not in ContentTypes:
            raise Error(f"Invalid content type {self._content} for GGXF file")
        self._needEpoch = self._content in TimeDependentContentTypes
        self._groups = []
        self._configured = False
        self._singleGroup = False
        self._source = source
        self._debug = False
        self._logger = logging.getLogger("GGXF")
        self._valueat = lambda xy, epoch, refepoch: None
        if debug:
            self.setDebug()
        self._parameters = [
            Parameter(paramdef) for paramdef in metadata.get(GGXF_ATTR_PARAMETERS, [])
        ]

    def setDebug(self, debug: bool = True):
        self._debug = debug
        self._logger.setLevel(logging.DEBUG if debug else logging.WARNING)
        for group in self._groups:
            group.setDebug(debug)

    def configure(self, errorhandler=None):
        self._singleGroup = len(self._groups) == 1
        ggxfParamSets = ContentTypes[self._content][ATTRDEF_PARAMSET_MAP]
        for param in self._parameters:
            if ggxfParamSets.get(param.name()) != param.set():
                self.logger().warn(
                    f'Non-standard parameter set "{param.set()}" for parameter "{param.name()}"'
                )
        for igroup, group in enumerate(self._groups):
            group.configure(id=str(igroup), errorhandler=errorhandler)

        self._nullvalue = [None for p in self._parameters]
        # Cached values for groups to use in calculation at epoch
        self._calcEpoch = None
        self._calcGroups = list(self.groups())
        self._zero = np.zeros((len(self._parameters),))
        self._configured = True

    def metadata(self, key=None):
        if key is not None:
            return self._metadata.get(key)
        return self._metadata

    def contentType(self):
        return self._content

    def needEpoch(self):
        return self._needEpoch

    def logger(self):
        return self._logger

    def parameters(self):
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

    def setFilename(self, filename):
        self._metadata["filename"] = filename

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

        if self._singleGroup:
            return self._groups[0].valueAt(xy, epoch, refepoch)

        if self._needEpoch:
            calcEpoch = (epoch, refepoch)
            if calcEpoch != self._calcEpoch:
                calcGroups = []
                for group in self.groups():
                    factor = group.timeFactorAt(epoch, refepoch)
                    if factor is not None and factor != 0.0:
                        calcGroups.append(group)
                self._calcEpoch = calcEpoch
                self._calcGroups = calcGroups
        if self._debug:
            self._logger.debug(
                f"Evaluating {len(self._calcGroups)} groups with non-zero time functions"
            )
        result = self._zero.copy()
        if len(self._calcGroups) == 0:
            return result
        for group in self._calcGroups:
            value = group.valueAt(xy, epoch, refepoch)
            if self._debug:
                self._logger.debug(f"{group.name()}: {value}")
            if value is not None:
                result += value
        return result

    def extents(self):
        grpext = np.array([g.extents() for g in self.groups()])
        return [
            [grpext[:, 0, 0].min(), grpext[:, 0, 1].min()],
            [grpext[:, 1, 0].max(), grpext[:, 1, 1].max()],
        ]

    def summary(self):
        metadata = self.metadata().copy()
        content = metadata.pop(GGXF_ATTR_CONTENT, "undefined")
        groups = [group.summary() for group in self.groups()]
        return {
            GGXF_ATTR_CONTENT: content,
            JSON_METADATA_ATTR: metadata,
            GGXF_ATTR_GGXF_GROUPS: groups,
        }

    def nodeCoordinateParameters(self):
        # Returns the names of the node coordinate parameters based on the
        # interpolation crs wkt
        return GGXF.nodeCoordinateParametersFromCrsWkt(
            self._metadata[GGXF_ATTR_INTERPOLATION_CRS_WKT]
        )

    @staticmethod
    def nodeCoordinateParametersFromCrsWkt(crswkt):
        # Crudely determine the node parameter names (in order) based on
        # an interpolation CRS
        #
        # Currently only supports GEOGCRS and PROJCRS

        try:
            crstype = re.match(r"^\s*(\w+)", crswkt).group(1)
            axis_directions = [
                m.group("direction")
                for m in re.finditer(
                    r"AXIS\[\s*\"(?P<name>[^\"]*)\"\s*\,\s*(?P<direction>\w+)",
                    crswkt,
                    re.S,
                )
            ]
        except:
            raise Error(f"Failed to interpret CRS WKT axes")
        axislookup = None
        for ctype, caxes in NODE_COORDINATE_PARAMETERS.items():
            if ctype in crstype.upper():
                axislookup = caxes
        if axislookup is None:
            raise Error(
                f"Failed to interpret CRS WKT: CRS type {crstype} not recognised"
            )
        # Currently only handling 2d interpolation CRS, but generously allow ignoring additional
        # height axis.  Possibly not valid?
        axis_directions = axis_directions[:2]
        if len(axis_directions) != 2:
            raise Error(f"Failed to interpret CRS WKT: WKT doesn't define two axes")
        try:
            nodeParams = [axislookup[d] for d in axis_directions]
        except KeyError as ex:
            raise Error(
                f"Failed to interpret CRS WKT: Unrecognized axis direction {ex}"
            )
        return nodeParams


class GridList:
    # A base class for Group and Grid, each of which may contain a list of grids.
    def __init__(self, name, metadata):
        self._id = None
        self._name = name
        self._metadata = metadata
        self._configured = False
        self._searchOrder = None
        self._grids = []

    def name(self):
        return self._name

    def id(self):
        return self._id

    def metadata(self):
        return self._metadata

    def setDebug(self, debug: bool = True):
        self._debug = debug
        for grid in self._grids:
            grid.setDebug(debug)

    def addGrid(self, grid: Grid):
        gridPriority = grid.priority()
        for sibling in self._grids:
            if sibling.overlaps(grid):
                siblingPriority = sibling.priority()
                if gridPriority is None or siblingPriority is None:
                    raise Error(
                        f"Overlapping sibling grids {sibling.name()} and {grid.name()} both need {GRID_ATTR_GRID_PRIORITY} defined"
                    )
                if grid.priority() == sibling.priority():
                    raise Error(
                        f"Sibling grids {sibling.name()} and {grid.name()} must have different {GRID_ATTR_GRID_PRIORITY}"
                    )
        self._grids.append(grid)
        self._configured = False

    def configure(self, id=None, errorhandler=None):
        if id:
            self._id = id
        for igrid, grid in enumerate(self._grids):
            grid.configure()
            if self._id:
                grid.setId(f"{self._id}:{igrid}")
        self._searchOrder = self._grids.copy()
        self._searchOrder.sort(key=lambda g: g.priority() or 0, reverse=True)
        self._configured = True

    def gridAt(self, xy):
        if not self._configured:
            raise Error("GGXF not configured")
        for grid in self._searchOrder:
            if grid.contains(xy):
                cgrid = grid.gridAt(xy) or grid
                return cgrid
        return None

    def grids(self):
        return self._grids

    def allgrids(self):
        for basegrid in self._grids:
            yield basegrid
            for grid in basegrid.allgrids():
                yield grid


class Group(GridList):
    def __init__(self, ggxf, groupname, metadata):
        super().__init__(groupname, metadata)
        self._ggxf = ggxf
        paramnames = metadata.get(GROUP_ATTR_GRID_PARAMETERS)
        if paramnames is None:
            paramnames = [p.name() for p in ggxf.parameters()]
        self._parameterNames = paramnames
        self._parameterMap = None
        self._zero = None
        method = metadata.get(GROUP_ATTR_INTERPOLATION_METHOD)
        self._interpolator = GridInterpolator.getMethod(method)
        self._grids = []
        self._timeFunction = None
        funcdeflist = metadata.get(GROUP_ATTR_TIME_FUNCTIONS)
        if funcdeflist is not None:
            self._timeFunction = CompoundTimeFunction()
            for funcdef in funcdeflist:
                self._timeFunction.addFunction(BaseTimeFunction.Create(funcdef))
        self._needEpoch = ggxf.needEpoch()
        self._cacheEpoch = ()
        self._cacheFactor = None
        self._debug = False

    def parameterNames(self):
        return self._parameterNames

    def nparam(self):
        return len(self._parameterNames)

    def ggxf(self):
        return self._ggxf

    def logger(self):
        return self._ggxf.logger()

    def configureParameters(self, errorhandler=None):
        ok = True
        # map the parameter names to the GGXF parameters
        paramset = set(self._parameterNames)
        ggxfparams = [p.name() for p in self._ggxf.parameters()]
        parammap = []
        for name in self._parameterNames:
            if name not in ggxfparams:
                error = f'Invalid parameter "{name}" in {GROUP_ATTR_GRID_PARAMETERS}'
                if errorhandler:
                    errorhandler(error)
                else:
                    raise Error(error)
                ok = False
            parammap.append(ggxfparams.index(name))
        # Check the set of parameters is valid for the content type

        contenttype = self._ggxf.contentType()
        contentdef = ContentTypes.get(contenttype)
        validparamsets = contentdef.get(ATTRDEF_PARAMETER_SETS, [])
        # Currently not supporting non GGXF parameters in a grid
        if paramset not in validparamsets:
            error = f"Invalid parameters ({','.join(paramset)}) for content type {contenttype}"
            if errorhandler:
                errorhandler(error)
            else:
                raise Error(error)
            ok = False
        if ok:
            # parameterSetIndices is a mapping from parameter sets to the
            # index into the parameters array for each element of the set
            self._parameters = [self._ggxf.parameters()[i] for i in parammap]
            paramSetIndices = {}
            for iparam, param in enumerate(self._parameters):
                if param.set() not in paramSetIndices:
                    paramSetIndices[param.set()] = []
                paramSetIndices[param.set()].append(iparam)
            self._paramSetIndices = paramSetIndices

            self._parameterMap = parammap
            self._zero = np.zeros((len(ggxfparams),))
        return ok

    def parameters(self):
        return self._parameters

    def paramSetIndices(self):
        return self._paramSetIndices

    def parameterMap(self):
        return self._parameterMap

    def valueAt(self, xy, epoch=None, refepoch=None):
        grid = self.gridAt(xy)
        if grid is None:
            return None
        if self._debug:
            self._ggxf._logger.debug(
                f"{self._name}: grid at {xy}: {grid.id()} {grid.name()}"
            )
        value = self._interpolator(grid, xy)
        if self._debug:
            self._ggxf._logger.debug(f"{self._name}: value at {xy}: {value}")
        if self._needEpoch:
            timeFactor = self.timeFactorAt(epoch, refepoch)
            if self._debug:
                self._ggxf._logger._debug(
                    f"{self.name}: time factor at {epoch} {refepoch}: {timeFactor:.4f}"
                )
            value *= timeFactor
        result = self._zero.copy()
        result[self._parameterMap] = value
        return result

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

    def extents(self):
        grdext = np.array([g.extents() for g in self.grids()])
        return [
            [grdext[:, 0, 0].min(), grdext[:, 0, 1].min()],
            [grdext[:, 1, 0].max(), grdext[:, 1, 1].max()],
        ]

    def summary(self):
        summary = self.metadata().copy()
        summary[GROUP_ATTR_GRID_PARAMETERS] = self.parameterNames()
        summary[GROUP_ATTR_GRIDS] = [grid.summary() for grid in self.allgrids()]
        return summary


class Grid(GridList):
    """
    GGXF grid component

    Note: Grid data is held as a numpy array of shape (ncol,nrow,nparam], so indexing is j,i,p
    """

    # As extents are calculated from floating point calculations need a tolerance in
    # containment and overlaps tests.  Tolerance is based on a multiple of the diagonal
    # length across a grid cell.

    TOLERANCE_RATIO = 0.00001

    def __init__(self, group: Group, gridname: str, metadata: dict, data=None):
        super().__init__(gridname, metadata)
        self._group = group
        if GRID_ATTR_DATA in self._metadata:
            if data is not None:
                raise Error(f"Multiple definitions of data for grid {gridname}")
            data = self._metadata.pop(GRID_ATTR_DATA)

        self._parent = None
        self._priority = metadata.get(GRID_ATTR_GRID_PRIORITY)
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
        diff = self.calcxy([0.0, 1.0]) - self.calcxy([1.0, 0.0])
        self._tolerance = np.sqrt(np.sum(diff * diff)) * self.TOLERANCE_RATIO
        self._xmin, self._ymin = range.min(axis=0)
        self._xmax, self._ymax = range.max(axis=0)
        self._debug = False

        self._data = None
        if data is not None:
            self.setData(data)

    def parent(self):
        return self._parent

    def group(self):
        return self._group

    def logger(self):
        return self._group.logger()

    def data(self):
        return self._data

    def priority(self):
        return self._priority

    def extents(self):
        return [[self._xmin, self._ymin], [self._xmax, self._ymax]]

    def size(self):
        return (self._imax + 1, self._jmax + 1)

    def setId(self, id):
        self._id = id
        for igrid, subgrid in enumerate(self.grids()):
            subgrid.setId(f"{id}:{igrid}")

    def addGrid(self, grid: Grid):
        gextents = grid.extents()
        dtol = self._tolerance
        gminxy = [gextents[0][0] + dtol, gextents[0][1] + dtol]
        gmaxxy = [gextents[1][0] - dtol, gextents[1][1] - dtol]
        if not self.contains(gminxy) or not self.contains(gmaxxy):
            raise Error(
                f"Grid {grid.name()} is not fully contained in parent {self.name()}"
            )
        grid._parent = self
        super().addGrid(grid)

    def setData(self, data):
        if type(data) not in (np.array, np.ma.masked_array):
            data = np.array(data)
        shape = (self._imax + 1, self._jmax + 1, self._nparam)
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

    def overlaps(self, grid: Grid):
        dtol = min(self._tolerance, grid._tolerance)
        if (
            self._xmin >= grid._xmax - dtol
            or self._xmax <= grid._xmin + dtol
            or self._ymin >= grid._ymax - dtol
            or self._ymax <= grid._ymin + dtol
        ):
            return False
        return True

    def maxij(self):
        return self._imax, self._jmax

    def cellij(self, xy):
        rij = self.calcij(xy)
        cij = np.maximum([0, 0], np.minimum(self._cellmax, np.floor(rij).astype(int)))
        cxy = rij - cij
        return cij, cxy

    def summary(self):
        "Returns a somewhat arbitrary summary of the grid contents"
        size = {"ngridi": self._imax + 1, "ngridj": self._jmax + 1}
        extents = {
            "xmin": float(self._xmin),
            "ymin": float(self._ymin),
            "xmax": float(self._xmax),
            "ymax": float(self._ymax),
        }
        params = self.group().parameterNames()
        pmin = self._data.min(axis=(0, 1))
        pmax = self._data.max(axis=(0, 1))
        pdata = {
            parami: {"min": float(pmini), "max": float(pmaxi)}
            for parami, pmini, pmaxi in zip(params, pmin, pmax)
        }
        summary = {
            "name": self.name(),
            "size": size,
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
        if grid._debug:
            grid._group._ggxf._logger.debug(
                f"{grid._name}: i,j={cellij[0]+cellxy[0]:.02f},{cellij[1]+cellxy[1]:.02f}"
            )
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
        nodeprm = data[nodes[:, 0], nodes[:, 1]]
        # Sum the scaled values to get the value at the evaluation point.
        val = (nodef * nodeprm).sum(axis=0)
        return val

    @staticmethod
    def biquadratic(grid: Grid, xy):
        # Evaluate the value of parameters at a point from grid nodes using biquadratic interpolation.
        # - determine which cell the point is in and the position cellxy of the point in the cell
        # (x,y coordinates ranging from 0 to 1)
        cellij, cellxy = grid.cellij(xy)
        if grid._debug:
            grid._group._ggxf._logger.debug(
                f"{grid._name}: i,j={cellij[0]+cellxy[0]:.02f},{cellij[1]+cellxy[1]:.02f}"
            )
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
        nodeprm = data[nodes[:, 0], nodes[:, 1]]
        # Sum the scaled values to get the value at the evaluation point.
        val = (nodef * nodeprm).sum(axis=0)
        return val

    @staticmethod
    def bicubic(grid: Grid, xy):
        # Evaluate the value of parameters at a point from grid nodes using biquadratic interpolation.
        # - determine which cell the point is in and the position cellxy of the point in the cell
        # (x,y coordinates ranging from 0 to 1)
        cellij, cellxy = grid.cellij(xy)
        if grid._debug:
            grid._group._ggxf._logger.debug(
                f"{grid._name}: i,j={cellij[0]+cellxy[0]:.02f},{cellij[1]+cellxy[1]:.02f}"
            )
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
        nodeprm = data[nodes[:, 0], nodes[:, 1]]
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
        self._set = metadata.get(PARAM_ATTR_PARAMETER_SET, self._name)
        axis = metadata.get(PARAM_ATTR_SOURCE_CRS_AXIS)
        self._sourceCrsAxis = axis if axis is not None and axis >= 0 else None
        self._unitName = metadata.get(PARAM_ATTR_UNIT_NAME, "")
        self._siRatio = float(metadata.get(PARAM_ATTR_UNIT_SI_RATIO, 1.0))
        self._minValue = metadata.get(PARAM_ATTR_PARAMETER_MINIMUM_VALUE)
        self._maxValue = metadata.get(PARAM_ATTR_PARAMETER_MAXIMUM_VALUE)
        self._noDataFlag = metadata.get(PARAM_ATTR_NO_DATA_FLAG)

    def name(self):
        return self._name

    def set(self):
        return self._set

    def sourceCrsAxis(self):
        return self._sourceCrsAxis

    def unitName(self):
        return self._unitName

    def siRatio(self):
        return self._siRatio

    def minValue(self):
        return self._minValue

    def maxValue(self):
        return self._maxValue

    def noDataFlag(self):
        return self._noDataFlag


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

    def write(self, ggxf, filename):
        raise NotImplementedError(
            f"{type(self).__name__} write function not implemented"
        )
