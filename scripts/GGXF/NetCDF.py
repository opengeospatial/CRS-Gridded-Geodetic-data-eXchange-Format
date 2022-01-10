#!/usr/bin/python3
#
#  Script to dump a single parameter from a single grid from a NetCDF4 XYZ file to an ASCII XYZ file
#
# Note: NetCDF is stored in column major order.  Ie dimensions ncol, nrow, nparam stores parameters for
# ncol, nrow consecutively.

import json
import logging
import os.path

import netCDF4
import numpy as np

from .GGXF import *

NETCDF_OPTION_METADATA_STYLE = "metadata_style"
NETCDF_METADATA_DOT0 = "dot0"
NETCDF_METADATA_DOT1 = "dot1"
NETCDF_METADATA_JSON = "json"

NETCDF_OPTION_GRID_DTYPE = "grid_dtype"
NETCDF_DTYPE_FLOAT32 = "float32"
NETCDF_DTYPE_FLOAT64 = "float64"

NETCDF_OPTION_USE_COMPOUND_TYPE = "use_compound_types"
NETCDF_OPTION_SIMPLIFY_1PARAM_GRIDS = "simplify_1param_grids"
NETCDF_OPTION_USE_NESTED_GRIDS = "use_nested_grids"
NETCDF_OPTION_WRITE_CDL = "write_cdl"

NETCDF_VAR_GRIDDATA = "data"

NETCDF_DIMENSION_GRIDI = "gridi"
NETCDF_DIMENSION_GRIDJ = "gridj"
NETCDF_DIMENSION_NPARAM = "parameter"

NETCDF_OPTIONS = f"""
The following options apply to NetCDF input (I) and output (O):

  "{NETCDF_OPTION_USE_NESTED_GRIDS}" (O) Generate NetCDF with nested grid definition (true or false, default true)
  "{NETCDF_OPTION_WRITE_CDL}" (O) Generate an output CDL file as well as a NetCDF file (default false)
  "{NETCDF_OPTION_USE_COMPOUND_TYPE}" (O) Use compound types (very limited test implementation) (default false)
"""
# "{NETCDF_OPTION_SIMPLIFY_1PARAM_GRIDS}" (O) Grids with just one parameter are created with just 2 dimensions (default false)


class Reader(BaseReader):
    @staticmethod
    def Read(ggxf_file: str, options: dict = None) -> GGXF:
        if not os.path.exists(ggxf_file):
            raise Error(f"GGXF file {ggxf_file} does not exist")
        reader = Reader(options)
        ggxf = reader.read(ggxf_file)
        return ggxf

    def __init__(self, options=None):
        BaseReader.__init__(self, options)
        self._logger = logging.getLogger("GGXF.NetCdfReader")

    def read(self, ggxf_file):
        self._logger.debug(f"Loading GGXF file {ggxf_file}")
        self.setSource(ggxf_file)
        try:
            root = netCDF4.Dataset(ggxf_file, "r", format="NETCDF4")
            metadata = self.loadMetadata(root)
            if self.validator().validateRootAttributes(metadata, context="GGXF"):
                ggxf = GGXF(metadata)
                for groupname, ncgroup in root.groups.items():
                    self.loadGroup(ggxf, groupname, ncgroup)
                ggxf.configure(errorhandler=self.loadError)
            if not self._loadok:
                ggxf = None
            return ggxf

        except Exception as ex:
            self._logger.error(f"Failed to load GGXF file {ggxf_file}: {ex}")
            ggxf = None
        return ggxf

    def loadGroup(self, ggxf, groupname, ncgroup):
        self._logger.debug(f"Loading group {groupname}")
        context = f"Group {groupname}"
        metadata = self.loadMetadata(ncgroup)
        if not self.validator().validateGroupAttributes(metadata, context=context):
            return
        group = Group(ggxf, groupname, metadata)
        for gridname, ncgrid in ncgroup.groups.items():
            self.loadGrid(group, gridname, ncgrid)
        ggxf.addGroup(group)

    def loadGrid(self, group, gridname, ncgrid, parent=None):
        self._logger.debug(f"Loading grid {gridname}")
        context = f"{group.name()} {gridname}"
        metadata = self.loadMetadata(ncgrid)
        if self.validator().validateGridAttributes(metadata, context=context):
            try:
                data = np.array(ncgrid[NETCDF_VAR_GRIDDATA])
            except Exception as ex:
                self.loadError("Cannot load data for grid {gridname}: {ex}")
                return
            grid = Grid(group, gridname, metadata, data)
            for gridname, ncsubgrid in ncgrid.groups.items():
                self.loadGrid(group, gridname, ncsubgrid, grid)
            if parent:
                parent.addGrid(grid)
            else:
                group.addGrid(grid)

    def loadMetadata(self, source):
        attrs = {}
        for key in source.ncattrs():
            value = source.getncattr(key)
            self._logger.debug(f"Loaded attr: {key}: {type(value)} {value}")
            attrs[key] = value
        # Handle JSON format for metadata.
        self._interpretDotMetadata(attrs)
        if JSON_METADATA_ATTR in attrs:
            jsonmeta = attrs.pop(JSON_METADATA_ATTR)
            try:
                meta = json.loads(jsonmeta)
                if not isinstance(meta, dict):
                    raise RuntimeError(f"{JSON_METADATA_ATTR} is not a dictionary")
                meta.update(attrs)
                attrs = meta
            except Exception as ex:
                self.loadError(f"Failed to load JSON metadata element: {ex}")
        return attrs

    def _interpretDotMetadata(self, attrs):
        # Convert numpy attributes to native python attributes
        for k, v in attrs.items():
            vtype = type(v)
            if vtype.__module__ == "numpy":
                if vtype == np.ndarray:
                    attrs[k] = v.tolist()
                else:
                    attrs[k] = v.item()

        arrays = []
        while True:
            compiled = {}
            for key, value in attrs.items():
                if "." not in key:
                    continue
                basekey, subkey = key.rsplit(".", maxsplit=1)
                compiled[basekey] = compiled.get(basekey, {})
                compiled[basekey][subkey] = value
            if not compiled:
                break
            for basekey, keyval in compiled.items():
                for subkey in keyval:
                    attrs.pop(basekey + "." + subkey)
                if "count" in keyval:
                    try:
                        arrsize = int(keyval["count"])
                        arrays.append((basekey, arrsize))
                    except:
                        self.loadError(f"Array {basekey} count is not an integer")

                if basekey in attrs and not isinstance(attrs[basekey], dict):
                    self.loadError(
                        f"Invalid duplicate attribute {basekey} and {basekey}.xxx"
                    )
                else:
                    attrs[basekey] = keyval

        # Process array in reverse order so always get embedded arrays before
        # enclosing array.  Convert from x={'count':n,'1':v1, ...} to x=[v1,...]
        for arrkey, arrsize in sorted(arrays, reverse=True):
            holder = attrs
            path = arrkey.split(".")
            item = path.pop()
            for key in path:
                holder = holder.get(key, {})
            if item not in holder:
                self.loadError(f"Cannot find array {arrkey}")
                continue
            arrval = holder[item]
            array = [arrval[str(i)] for i in range(arrsize + 1) if str(i) in arrval]
            if len(array) != arrsize:
                self.loadError(
                    f"Array {arrkey} does not have the correct number of items: expect {arrsize}, got {len(array)}"
                )
            else:
                holder[item] = array


class Writer(BaseWriter):
    @staticmethod
    def Write(ggxf, ggxf_file, options=None):
        writer = Writer(options)
        writer.write(ggxf, ggxf_file)

    def __init__(self, options=None):
        BaseWriter.__init__(self, options)
        self._logger = logging.getLogger("GGXF.NetCdfWriter")

    def write(self, ggxf, netcdf4_file: str):
        metastyle = self.getOption(NETCDF_OPTION_METADATA_STYLE, NETCDF_METADATA_DOT0)
        if metastyle == NETCDF_METADATA_JSON:
            self._logger.debug("Using JSON metadata format")
            metafunc = lambda dataset, entity, exclude: self.saveNetCdf4MetdataJson(
                dataset, entity, exclude=exclude
            )
        elif metastyle == NETCDF_METADATA_DOT1:
            self._logger.debug('Using base 1 "dot" format metadata')
            metafunc = lambda dataset, entity, exclude: self.saveNetCdf4MetdataDot(
                dataset, entity, exclude=exclude, base=1
            )
        else:  # Default is dot0, also used with cdf4 compound types
            self._logger.debug('Using base 0 "dot" format metadata')
            metafunc = lambda dataset, entity, exclude: self.saveNetCdf4MetdataDot(
                dataset, entity, exclude=exclude, base=0
            )
        self._useCompoundTypes = self.getBoolOption(
            NETCDF_OPTION_USE_COMPOUND_TYPE, False
        )
        if self._useCompoundTypes:
            self._logger.warning("Using NetCDF4 compound types (experimental)")
        self._useNestedGrids = self.getBoolOption(NETCDF_OPTION_USE_NESTED_GRIDS, True)
        self._logger.debug(f"Using nested grid structure: {self._useNestedGrids}")
        # Not currently implemented.
        # self._simplify1ParamGrids = self.getBoolOption(
        #     NETCDF_OPTION_SIMPLIFY_1PARAM_GRIDS, False
        # )
        # self._logger.debug(
        #     f"Simplifying grids with just 1 param per node: {self._simplify1ParamGrids}"
        # )
        dtype = self.getOption(NETCDF_OPTION_GRID_DTYPE, NETCDF_DTYPE_FLOAT32)
        self._dtype = dtype = (
            np.float64 if dtype == NETCDF_DTYPE_FLOAT64 else np.float32
        )
        self._saveMetadata = metafunc

        self._logger.debug(f"Saving NetCDF4 grid as {netcdf4_file}")
        if os.path.isfile(netcdf4_file):
            os.remove(netcdf4_file)
        root = netCDF4.Dataset(netcdf4_file, "w", format="NETCDF4")
        self.saveGgxfNetCdf4(root, ggxf)
        root.close()
        if self.getBoolOption(NETCDF_OPTION_WRITE_CDL):
            root = netCDF4.Dataset(netcdf4_file, "r", format="NETCDF4")
            cdl_file = os.path.splitext(netcdf4_file)[0] + ".cdl"
            root.tocdl(data=True, outfile=cdl_file)

    def saveGgxfNetCdf4(self, root, ggxf):
        nctypes = {}

        # NetCDF compound types
        if self._useCompoundTypes:
            paramtype = np.dtype(
                [("parameterName", "S32"), ("unit", "S16"), ("unitSiRatio", np.float64)]
            )
            ncparamtype = root.createCompoundType(paramtype, "ggxfParameterType")
            nctypes["ggxfParameterType"] = GGXF.RecordType(paramtype, ncparamtype)

        self._saveMetadata(
            root, ggxf.metadata(), [GGXF_ATTR_GROUPS, GGXF_ATTR_GRID_DATA]
        )

        # Store each of the groups
        for group in ggxf.groups():
            self.saveGroupNetCdf4(root, group, nctypes)

    def saveGroupNetCdf4(self, root: netCDF4.Dataset, group: dict, nctypes: dict):
        name = group.name()
        cdfgroup = root.createGroup(name)
        exclude = [GROUP_ATTR_GROUP_NAME, GROUP_ATTR_GRIDS]

        # Store group attributes
        parameters = group.parameters()
        nparam = len(parameters)

        cdfgroup.createDimension(NETCDF_DIMENSION_NPARAM, nparam)
        if self._useCompoundTypes:
            paramdata = [(p.name(), p.units(), p.siratio()) for p in parameters]
            paramtype = nctypes["ggxfParameterType"]
            paramdata = np.array(paramdata, dtype=paramtype.dtype)
            paramvar = cdfgroup.createVariable(
                "parameters", paramtype.netcdfType, NETCDF_DIMENSION_NPARAM
            )
            paramvar[:] = paramdata
            exclude.append(GROUP_ATTR_PARAMETERS)

        self._saveMetadata(cdfgroup, group.metadata(), exclude)

        # Store each of the grids
        grids = group.grids() if self._useNestedGrids else group.allgrids()
        for grid in grids:
            self.saveGridNetCdf4(cdfgroup, grid, nctypes, nparam)

    def saveGridNetCdf4(
        self, cdfgroup: netCDF4.Group, grid: dict, nctypes: dict, nparam: int
    ):
        name = grid.name()
        cdfgrid = cdfgroup.createGroup(name)
        exclude = [
            GRID_ATTR_GRID_NAME,
            GRID_ATTR_GRIDS,
            GRID_ATTR_DATA,
            GRID_ATTR_DATA_SOURCE,
            GRID_ATTR_AFFINE_COEFFS,
        ]

        if grid.parent() and not self._useNestedGrids:
            grid.metadata()[GRID_ATTR_PARENT_GRID_NAME] = grid.parent().name()
        else:
            exclude.append(GRID_ATTR_PARENT_GRID_NAME)

        # Store the grid metadata
        # affinevar=cdfgrid.createVariable('affineCoeffs',np.float64,'affine')
        # self._logger.debug(f"Filling affineCoeffs {affinevar.shape} {affinevar.datatype} from {grid['affineCoeffs']}")
        # affinevar[:]=np.array(grid['affineCoeffs'])

        size = grid.size()
        cdfgrid.createDimension(NETCDF_DIMENSION_GRIDI, size[0])
        cdfgrid.createDimension(NETCDF_DIMENSION_GRIDJ, size[1])

        # Store the grid data
        datavar = cdfgrid.createVariable(
            NETCDF_VAR_GRIDDATA,
            self._dtype,
            [NETCDF_DIMENSION_GRIDJ, NETCDF_DIMENSION_GRIDI, NETCDF_DIMENSION_NPARAM],
        )
        datavar[:, :, :] = grid.data()
        metadata = grid.metadata()
        self._saveMetadata(cdfgrid, metadata, exclude)
        cdfgrid.setncatts({GRID_ATTR_AFFINE_COEFFS: metadata[GRID_ATTR_AFFINE_COEFFS]})

        # Support for nested grid possibility
        if self._useNestedGrids:
            for subgrid in grid.subgrids():
                self.saveGridNetCdf4(cdfgrid, subgrid, nctypes, nparam)

    def saveNetCdf4MetdataDot(
        self,
        dataset: netCDF4.Dataset,
        entity,
        name: str = "",
        exclude=[],
        base: int = 0,
    ) -> None:
        if type(entity) == dict:
            if name != "":
                name = name + "."
            for key, value in entity.items():
                if key not in exclude and not key.startswith("_"):
                    self.saveNetCdf4MetdataDot(dataset, value, name + key, base=base)
        elif type(entity) == list:
            count = int(len(entity))
            self.saveNetCdf4MetdataDot(dataset, count, name + ".count")
            for ival, value in enumerate(entity):
                self.saveNetCdf4MetdataDot(dataset, value, name + f".{ival+base}")
        else:
            try:
                dataset.setncattr(name, entity)
            except Exception as ex:
                raise RuntimeError(f"Cannot save {name}: {ex}")

    def saveNetCdf4MetdataJson(
        self,
        dataset: netCDF4.Dataset,
        entity: dict,
        name="metadata",
        exclude=[],
        indent=2,
    ):
        value = {
            k: v
            for k, v in entity.items()
            if k not in exclude and not k.startswith("_")
        }
        value = json.dumps(value, indent=indent)
        dataset.setncattr(name, value)
