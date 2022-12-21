#!/usr/bin/python3
#
# NetCDF implementation of GGXF.
#
# Note: NetCDF is stored in column major order.  Ie dimensions ncol, nrow, nparam stores parameters for
# ncol, nrow consecutively.
#
# Note: relying on Python API to handle implementation of missing_value, add_offset, and scale_factor

import logging
import os.path

import netCDF4
import numpy as np

from .GGXF import *

NETCDF_OPTION_GRID_DTYPE = "grid_dtype"
NETCDF_DTYPE_FLOAT32 = "float32"
NETCDF_DTYPE_FLOAT64 = "float64"
NETCDF_DTYPE_INT32 = "int32"
NETCDF_DTYPE_INT16 = "int16"
NETCDF_VALID_DTYPE_MAP = {
    NETCDF_DTYPE_FLOAT64: np.float64,
    NETCDF_DTYPE_FLOAT32: np.float32,
    NETCDF_DTYPE_INT32: np.int32,
    NETCDF_DTYPE_INT16: np.int16,
}
NETCDF_DEFAULT_WRITE_DTYPE = NETCDF_DTYPE_FLOAT32
NETCDF_DEFAULT_READ_DTYPE = NETCDF_DTYPE_FLOAT64

NETCDF_OPTION_WRITE_CDL = "write-cdl"
NETCDF_OPTION_PACK_PRECISION = "packing-precision"

NETCDF_CDL_OPTION_FULL = "full"
NETCDF_CDL_OPTION_HEADER = "header"
NETCDF_CDL_OPTION_NONE = "none"

NETCDF_CONVENTIONS_ATTRIBUTE = "Conventions"
NETCDF_CONVENTIONS_VALUE = "{ggxfVersion}, ACDD-1.3"

NETCDF_DIMENSION_GRIDI = "iNodeCount"
NETCDF_DIMENSION_GRIDJ = "jNodeCount"

NETCDF_ATTR_CONTEXT_GGXF = "ggxf"
NETCDF_ATTR_CONTEXT_GROUP = "group"
NETCDF_ATTR_CONTEXT_GRID = "grid"

NETCDF_READ_OPTIONS = f"""
  "{NETCDF_OPTION_GRID_DTYPE}" Specifies the data type used for the grid ({", ".join(NETCDF_VALID_DTYPE_MAP.keys())})

  When reading a NetCDF file the default floating point is {NETCDF_DEFAULT_READ_DTYPE} to avoid rounding issues.
"""

NETCDF_WRITE_OPTIONS = f"""
  "{NETCDF_OPTION_GRID_DTYPE}" Specifies the data type in the NetCDF file ({", ".join(NETCDF_VALID_DTYPE_MAP.keys())})
  "{NETCDF_OPTION_WRITE_CDL}" Generate an output CDL file as well as a NetCDF file ({NETCDF_CDL_OPTION_FULL}, {NETCDF_CDL_OPTION_HEADER}, or {NETCDF_CDL_OPTION_NONE})
  "{NETCDF_OPTION_PACK_PRECISION}" Specifies integer packing using specified number of decimal places

  If {NETCDF_OPTION_PACK_PRECISION} is specified then {NETCDF_OPTION_GRID_DTYPE} is ignored and integer packing
  is attempted.  If an integer data type is specified then the data will be scaled to fill the range available
  with the integer type.  If neither is specified {NETCDF_DEFAULT_WRITE_DTYPE} is used.
"""
#  "{NETCDF_OPTION_SIMPLIFY_1PARAM_GRIDS}" (O) Grids with just one parameter are created with just 2 dimensions (default false)

ACDD_AttributeMapping = {
    "title": "title",
    "abstract": "summary",
    "filename": "source_file",
    "electronicMailAddress": "creator_email",
    "partyName": "institution",
    "publicationDate": "date_issued",
    "onlineResourceLinkage": "publisher_url",
    "version": "product_version",
    "contentApplicabilityExtent.boundingBox.southBoundLatitude": "geospatial_lat_min",
    "contentApplicabilityExtent.boundingBox.westBoundLongitude": "geospatial_lon_min",
    "contentApplicabilityExtent.boundingBox.northBoundLatitude": "geospatial_lat_max",
    "contentApplicabilityExtent.boundingBox.eastBoundLongitude": "geospatial_lon_max",
    "contentApplicabilityExtent.extentDescription": "extent_description",
    "contentApplicabilityExtent.boundingPolygon": "geospatial_bounds",
    "contentApplicabilityExtent.extentTemporal.endDate": "end_date",
    "contentApplicabilityExtent.extentTemporal.startDate": "start_date",
    "contentApplicabilityExtent.extentVertical.extentVerticalCrsWkt": "vertical_extent_crs_wkt",
    "contentApplicabilityExtent.extentVertical.extentVerticalMaximum": "vertical_extent_maximum",
    "contentApplicabilityExtent.extentVertical.extentVerticalMinimum": "vertical_extent_minimum",
    "contentApplicabilityExtent.extentDescription": "extent_description",
    "contentBox.eastBoundLongitude": "east_bound_longitude",
    "contentBox.northBoundLatitude": "north_bound_latitude",
    "contentBox.southBoundLatitude": "south_bound_latitude",
    "contentBox.westBoundLongitude": "west_bound_longitude",
    "identifier.codeSpace": "DOI",
}

ReverseACCD_AttributeMapping = {v: k for k, v in ACDD_AttributeMapping.items()}


def _camelCase(attr):
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), attr)


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
            dtypestr = self.getOption(
                NETCDF_OPTION_GRID_DTYPE, NETCDF_DEFAULT_READ_DTYPE
            )
            self._dtype = NETCDF_VALID_DTYPE_MAP.get(dtypestr)
            if self._dtype is None:
                raise RuntimeError(
                    f"Invalid {NETCDF_OPTION_GRID_DTYPE} option {dtypestr}"
                )
            if not np.issubdtype(self._dtype, np.floating):
                raise RuntimeError(
                    f"Data type {dtypestr} not a floating point type: invalid for reading a NetCDF "
                )

            root = netCDF4.Dataset(ggxf_file, "r", format="NETCDF4")
            metadata = self.loadMetadata(NETCDF_ATTR_CONTEXT_GGXF, root)
            # Handle something in python/netcdf handling which doesn't distinguish
            # between a list of 1 element and a scalar.
            if isinstance(metadata.get(GGXF_ATTR_PARAMETERS), dict):
                metadata[GGXF_ATTR_PARAMETERS] = [metadata[GGXF_ATTR_PARAMETERS]]

            if self.validator().validateRootAttributes(metadata, context="GGXF"):
                ggxf = GGXF(metadata)
                for groupname, ncgroup in root.groups.items():
                    group = self.loadGroup(ggxf, groupname, ncgroup)
                    ggxf.addGroup(group)
                ggxf.configure(errorhandler=self.error)
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
        metadata = self.loadMetadata(NETCDF_ATTR_CONTEXT_GROUP, ncgroup)
        # gridParameters is expecting an array of values but NetCDF reader converts
        # to scalar if there is only 1
        if "gridParameters" in metadata and type(metadata["gridParameters"]) == str:
            metadata["gridParameters"] = [metadata["gridParameters"]]
        if not self.validator().validateGroupAttributes(metadata, context=context):
            return
        group = Group(ggxf, groupname, metadata)
        group.configureParameters(self.error)
        self.addGrids(group, ncgroup, group)
        return group

    def addGrids(self, group, ncgroup, target):
        for gridname, ncgrid in ncgroup.groups.items():
            grid = self.loadGrid(group, gridname, ncgrid)
            if grid is not None:
                target.addGrid(grid)

    def loadGrid(self, group, gridname, ncgrid):
        self._logger.debug(f"Loading grid {gridname}")
        context = f"{group.name()} {gridname}"
        metadata = self.loadMetadata(NETCDF_ATTR_CONTEXT_GRID, ncgrid)
        grid = None

        # Handling of sets in NetCDF reader/writer, mapping to/from
        # single array.  Implemented in NetCDF reader as short term
        # approach.  Ultimately want parameter sets in GGXF definition
        # to support lazy loading of grids.
        data = None
        try:
            for pset, pindices in group.paramSetIndices().items():
                try:
                    ncdata = ncgrid[pset]
                #                   sdata = np.ma.masked_array(ncdata)
                except Exception as ex:
                    self.error(
                        f"Cannot load data for grid {gridname} parameter set {pset}: {ex}"
                    )
                    return
                # if len(sdata.shape) == 2:
                #     shape = [*data.shape, 1]
                #     print(sdata)
                #     rsdata = sdata.reshape(shape)
                #     sdata = rsdata
                if data is None:
                    data = np.ma.masked_all(
                        (ncdata.shape[0], ncdata.shape[1], group.nparam()),
                        dtype=self._dtype,
                    )
                if len(ncdata.shape) == 2:
                    data[:, :, pindices[0]] = np.ma.masked_array(ncdata)
                else:
                    data[:, :, pindices] = np.ma.masked_array(ncdata)

        except Exception as ex:
            self.error(f"Cannot compile grid data for grid {gridname}: {ex}")

        if np.count_nonzero(data.mask) == 0:
            data = data.data

        metadata[GRID_ATTR_I_NODE_COUNT] = data.shape[0]
        metadata[GRID_ATTR_J_NODE_COUNT] = data.shape[1]

        if self.validator().validateGridAttributes(metadata, context=context):
            grid = Grid(group, gridname, metadata, data)
            self.addGrids(group, ncgrid, grid)
        return grid

    def loadMetadata(self, context: str, source):
        attrs = {}
        for key in source.ncattrs():
            value = source.getncattr(key)
            self._logger.debug(f"Loaded attr: {key}: {type(value)} {value}")
            attrs[key] = value
        attrs = self._convertNumpyAttributesToNative(attrs)
        attrs = self._mapAttributesToDotted(context, attrs)
        self._interpretDotMetadata(attrs)
        return attrs

    def _mapAttributesToDotted(self, context: str, attrs):
        mapped = {}
        for key, value in attrs.items():
            if key == NETCDF_CONVENTIONS_ATTRIBUTE:
                key = GGXF_ATTR_GGXF_VERSION
                match = re.match(r".*(GGXF\-[^,\s]+)", value)
                value = match.group(1) if match else ""
            elif (
                context == NETCDF_ATTR_CONTEXT_GGXF
                and key in ReverseACCD_AttributeMapping
            ):
                key = ReverseACCD_AttributeMapping[key]
            else:
                key = _camelCase(key)
            mapped[key] = value
        return mapped

    def _convertNumpyAttributesToNative(self, attrs):
        # Convert numpy attributes to native python attributes
        return {k: self._convertNumpyToNative(v) for k, v in attrs.items()}

    def _convertNumpyToNative(self, v):
        vtype = type(v)
        if vtype.__module__ == "numpy":
            fields = v.dtype.fields
            if vtype == np.ndarray:
                if fields:
                    return [self._convertNumpyToNative(vn) for vn in v]
                v = v.tolist()
            else:
                if fields:
                    # Awkward handling of null value in parameter type for floating point fields
                    # (eg parameterMinimumValue).  Remove parameters floating point parameters matching
                    # the minimum value of their dtype.  Probably a better way to do this!
                    #
                    # Assume integer values are actually counts so treat negative as equivalent to null.
                    result = {}
                    for field in fields:
                        fval = v[field]
                        if fval.dtype.kind == "f" and fval == np.finfo(fval.dtype).min:
                            continue
                        if fval.dtype.kind == "i" and fval < 0:
                            continue
                        if fval.dtype.kind == "S" and fval == "":
                            continue
                        result[field] = self._convertNumpyToNative(fval)
                    v = result
                else:
                    v = v.item()
                    if type(v) == bytes:
                        v = v.decode("utf8")
        return v

    def _interpretDotMetadata(self, attrs):
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
                        self.error(f"Array {basekey} count is not an integer")

                if basekey in attrs and not isinstance(attrs[basekey], dict):
                    self.error(
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
                self.error(f"Cannot find array {arrkey}")
                continue
            arrval = holder[item]
            array = [arrval[str(i)] for i in range(arrsize + 1) if str(i) in arrval]
            if len(array) != arrsize:
                self.error(
                    f"Array {arrkey} does not have the correct number of items: expect {arrsize}, got {len(array)}"
                )
            else:
                holder[item] = array


class NetCdfWriterError(RuntimeError):
    pass


class Writer(BaseWriter):
    @staticmethod
    def Write(ggxf, ggxf_file, options=None):
        writer = Writer(options)
        writer.write(ggxf, ggxf_file)

    def __init__(self, options=None):
        BaseWriter.__init__(self, options)
        self._logger = logging.getLogger("GGXF.NetCdfWriter")

    def write(self, ggxf, netcdf4_file: str):
        dtypestr = self.getOption(NETCDF_OPTION_GRID_DTYPE, NETCDF_DEFAULT_WRITE_DTYPE)
        self._dtype = NETCDF_VALID_DTYPE_MAP.get(dtypestr)
        if self._dtype is None:
            raise NetCdfWriterError(
                f"Invalid {NETCDF_OPTION_GRID_DTYPE} option {dtypestr}"
            )
        self._autopackPrecision = None
        self._autopackScale = None
        precision = self.getOption(NETCDF_OPTION_PACK_PRECISION)
        if precision is not None:
            try:
                precision = int(precision)
                if precision > 20 or precision < 0:
                    raise RuntimeError
                self._autopackPrecision = precision
                self._autopackScale = 10.0**precision
            except:
                raise NetCdfWriterError(
                    f"Invalid value for {NETCDF_OPTION_PACK_PRECISION}"
                )

        self._logger.debug(f"Saving NetCDF4 grid as {netcdf4_file}")
        if os.path.isfile(netcdf4_file):
            os.remove(netcdf4_file)
        root = netCDF4.Dataset(netcdf4_file, "w", format="NETCDF4")
        filename = os.path.basename(netcdf4_file)
        ggxf.setFilename(filename)
        self.saveGgxfNetCdf4(root, ggxf)
        root.close()
        cdloption = self.getOption(NETCDF_OPTION_WRITE_CDL).lower()
        if cdloption == NETCDF_CDL_OPTION_FULL or cdloption == NETCDF_CDL_OPTION_HEADER:
            root = netCDF4.Dataset(netcdf4_file, "r", format="NETCDF4")
            cdl_file = os.path.splitext(netcdf4_file)[0] + ".cdl"
            data = cdloption == NETCDF_CDL_OPTION_FULL
            root.tocdl(data=data, outfile=cdl_file)

    def saveGgxfNetCdf4(self, root, ggxf):
        nctypes = {}
        exclude = [GGXF_ATTR_GGXF_GROUPS]
        converted = {}
        self.saveNetCdf4MetdataDot(
            NETCDF_ATTR_CONTEXT_GGXF,
            root,
            ggxf.metadata(),
            exclude=exclude,
            converted=converted,
        )

        # Store each of the groups
        for group in ggxf.groups():
            self.saveGroupNetCdf4(root, group, nctypes)

    def saveGroupNetCdf4(self, root: netCDF4.Dataset, group: dict, nctypes: dict):
        name = group.name()
        cdfgroup = root.createGroup(name)
        exclude = [GROUP_ATTR_GGXF_GROUP_NAME, GROUP_ATTR_GRIDS]

        # Store group attributes
        parameters = group.parameterNames()
        nparam = len(parameters)

        for pset, pindices in group.paramSetIndices().items():
            if len(pindices) > 1:
                cdfgroup.createDimension(f"{pset}Count", len(pindices))

        self.saveNetCdf4MetdataDot(
            NETCDF_ATTR_CONTEXT_GROUP, cdfgroup, group.metadata(), exclude=exclude
        )

        # Store each of the grids
        for grid in group.grids():
            self.saveGridNetCdf4(cdfgroup, group, grid, nctypes, nparam)

    def saveGridNetCdf4(
        self,
        cdfgroup: netCDF4.Group,
        group: dict,
        grid: dict,
        nctypes: dict,
        nparam: int,
    ):
        name = grid.name()
        cdfgrid = cdfgroup.createGroup(name)
        exclude = [
            GRID_ATTR_GRID_NAME,
            GRID_ATTR_CHILD_GRIDS,
            GRID_ATTR_DATA,
            GRID_ATTR_DATA_SOURCE,
            GRID_ATTR_I_NODE_COUNT,
            GRID_ATTR_J_NODE_COUNT,
            #            GRID_ATTR_AFFINE_COEFFS,
        ]

        size = grid.size()
        cdfgrid.createDimension(NETCDF_DIMENSION_GRIDI, size[0])
        cdfgrid.createDimension(NETCDF_DIMENSION_GRIDJ, size[1])

        # Store the grid data

        for pset, pindices in group.paramSetIndices().items():
            vardata = grid.data()[:, :, pindices]
            (vartype, varattr) = self.variableAttributes(vardata)
            dimensions = [NETCDF_DIMENSION_GRIDI, NETCDF_DIMENSION_GRIDJ]
            if len(pindices) > 1:
                dimensions.append(f"{pset}Count")

            datavar = cdfgrid.createVariable(
                pset,
                vartype,
                dimensions,
            )
            if varattr:
                datavar.setncatts(varattr)

            if len(pindices) > 1:
                datavar[:, :, :] = vardata
            else:
                datavar[:, :] = vardata[:, :, 0]

        metadata = grid.metadata()
        self.saveNetCdf4MetdataDot(
            NETCDF_ATTR_CONTEXT_GRID, cdfgrid, metadata, exclude=exclude
        )

        # Support for nested grid possibility
        for subgrid in grid.grids():
            self.saveGridNetCdf4(cdfgrid, group, subgrid, nctypes, nparam)

    def variableAttributes(self, vardata):
        masked = False
        datacount = vardata.size
        if isinstance(vardata, np.ma.masked_array):
            maskcount = np.count_nonzero(vardata.mask)
            datacount -= maskcount
            masked = maskcount > 0
        dtype = self._dtype
        add_offset = None
        scale_factor = None
        if self._autopackPrecision is not None:
            if datacount == 0:
                dtype = np.int16
            else:
                range = np.max(vardata)
                midrange = (range + np.min(vardata)) / 2.0
                range -= midrange
                range = range * self._autopackScale
                for itype in (np.int16, np.int32):
                    imax = np.iinfo(itype).max
                    # Small tolerance to allow for a missing value
                    if imax - 2 > range:
                        dtype = itype
                        scale_factor = self._autopackScale
                        add_offset = round(midrange, self._autopackPrecision)
                        break
        elif np.issubdtype(dtype, np.integer) and datacount > 0:
            range = np.max(vardata)
            add_offset = (np.min(vardata) + range) / 2.0
            range -= add_offset
            nmax = np.iinfo(dtype).max
            scale_factor = range / (nmax - 2)

        varattr = {}
        if add_offset is not None:
            varattr["add_offset"] = add_offset
        if scale_factor is not None:
            varattr["scale_factor"] = 1.0 / scale_factor
        if masked:
            if np.issubdtype(dtype, np.integer):
                varattr["missing_value"] = np.array([np.iinfo(dtype).max], dtype=dtype)
            else:
                varattr["missing_value"] = np.array([np.finfo(dtype).max], dtype=dtype)

        return dtype, varattr

    def saveNetCdf4Attr(self, context: str, dataset: netCDF4.Dataset, name: str, value):
        if name == GGXF_ATTR_GGXF_VERSION:
            name = NETCDF_CONVENTIONS_ATTRIBUTE
            value = NETCDF_CONVENTIONS_VALUE.replace("{ggxfVersion}", value)
        elif context == NETCDF_ATTR_CONTEXT_GGXF and name in ACDD_AttributeMapping:
            name = ACDD_AttributeMapping[name]
        if type(value) == str:
            value = value.encode("utf8")
        dataset.setncattr(name, value)

    def saveNetCdf4MetdataDot(
        self,
        context: str,
        dataset: netCDF4.Dataset,
        entity,
        name: str = "",
        exclude=[],
        converted={},
        base: int = 0,
    ) -> None:
        if type(entity) == dict:
            if name != "":
                name = name + "."
            for key, value in entity.items():
                if key in converted:
                    self.saveNetCdf4Attr(context, dataset, key, converted[key])
                elif key not in exclude and not key.startswith("_"):
                    self.saveNetCdf4MetdataDot(
                        context, dataset, value, name + key, base=base
                    )
        elif type(entity) == list:
            listtypes = set((type(e) for e in entity))
            # Simple lists can be held as 1 dimensional array parameters
            if listtypes == set((str,)) or listtypes <= set((float, int)):
                self.saveNetCdf4Attr(context, dataset, name, entity)
            else:
                count = int(len(entity))
                self.saveNetCdf4MetdataDot(context, dataset, count, name + ".count")
                for ival, value in enumerate(entity):
                    self.saveNetCdf4MetdataDot(
                        context, dataset, value, name + f".{ival+base}"
                    )
        else:
            try:
                self.saveNetCdf4Attr(context, dataset, name, entity)
            except Exception as ex:
                raise NetCdfWriterError(f"Cannot save {name}: {ex}")
