#!/usr/bin/python3
#
# NetCDF implementation of GGXF.
#
# Note: NetCDF is stored in column major order.  Ie dimensions ncol, nrow, nparam stores parameters for
# ncol, nrow consecutively.

import json
import logging
import os.path

import netCDF4
import numpy as np

from .GGXF import *

NETCDF_OPTION_GRID_DTYPE = "grid_dtype"
NETCDF_DTYPE_FLOAT32 = "float32"
NETCDF_DTYPE_FLOAT64 = "float64"

NETCDF_OPTION_USE_COMPOUND_TYPE = "use_compound_types"
NETCDF_OPTION_USE_SNAKE_CASE_ATTRIBUTES = "use_snake_case_attributes"
NETCDF_OPTION_SIMPLIFY_1PARAM_GRIDS = "simplify_1param_grids"
NETCDF_OPTION_WRITE_CDL = "write_cdl"
NETCDF_OPTION_WRITE_CDL_HEADER = "write_cdl_header"

NETCDF_CONVENTIONS_ATTRIBUTE = "Conventions"
NETCDF_CONVENTIONS_VALUE = "{ggxfVersion}, ACDD-1.3"


NETCDF_VAR_GRIDDATA = "data"

NETCDF_DIMENSION_GRIDI = "gridi"
NETCDF_DIMENSION_GRIDJ = "gridj"
NETCDF_DIMENSION_NPARAM = "parameter"

NETCDF_ATTR_CONTEXT_GGXF = "ggxf"
NETCDF_ATTR_CONTEXT_GROUP = "group"
NETCDF_ATTR_CONTEXT_GRID = "grid"

NETCDF_OPTIONS = f"""
The following options apply to NetCDF input (I) and output (O):

  "{NETCDF_OPTION_USE_SNAKE_CASE_ATTRIBUTES}" (O) Convert attributes to snake_case (default false)"
  "{NETCDF_OPTION_WRITE_CDL}" (O) Generate an output CDL file as well as a NetCDF file (default false)
  "{NETCDF_OPTION_WRITE_CDL_HEADER}" (O) Only write the header information in the CDL file (default false)
  "{NETCDF_OPTION_USE_COMPOUND_TYPE}" (O) Use compound types (very limited test implementation) (default false)
"""
#  "{NETCDF_OPTION_SIMPLIFY_1PARAM_GRIDS}" (O) Grids with just one parameter are created with just 2 dimensions (default false)

ACDD_AttributeMapping = {
    "title": "title",
    "abstract": "summary",
    "filename": "source_file",
    "electronicMailAddress": "creator_email",
    "partyName": "publisher_institution",
    "publicationDate": "date_issued",
    "onlineResourceLinkage": "publisher_url",
    "version": "product_version",
    "contentApplicabilityExtent.boundingBox.southBoundLatitude": "geospatial_lat_min",
    "contentApplicabilityExtent.boundingBox.westBoundLongitude": "geospatial_lon_min",
    "contentApplicabilityExtent.boundingBox.northBoundLatitude": "geospatial_lat_max",
    "contentApplicabilityExtent.boundingBox.eastBoundLongitude": "geospatial_lon_max",
    "contentApplicabilityExtent.extentDescription": "extent_description",
    "contentApplicabilityExtent.boundingPolygon": "geospatial_bounds",
    "contentApplicabilityExtent.temporalExtent.endDate": "end_date",
    "contentApplicabilityExtent.temporalExtent.startDate": "start_date",
    "contentApplicabilityExtent.verticalExtent.verticalExtentCrsWkt": "vertical_extent_crs_wkt",
    "contentApplicabilityExtent.verticalExtent.verticalExtentMaximum": "vertical_extent_maximum",
    "contentApplicabilityExtent.verticalExtent.verticalExtentMinimum": "vertical_extent_minimum",
    "contentApplicabilityExtent.extentDescription": "extent_description",
    "contentBox.eastBoundLongitude": "east_bound_longitude",
    "contentBox.northBoundLatitude": "north_bound_latitude",
    "contentBox.southBoundLatitude": "south_bound_latitude",
    "contentBox.westBoundLongitude": "west_bound_longitude",
}

ReverseACCD_AttributeMapping = {v: k for k, v in ACDD_AttributeMapping.items()}


def _snakeCase(attr):
    attr = re.sub(
        r"([a-z0-9])([A-Z])", lambda m: m.group(1) + "_" + m.group(2).lower(), attr
    )
    return attr.lower()


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
            root = netCDF4.Dataset(ggxf_file, "r", format="NETCDF4")
            metadata = self.loadMetadata(NETCDF_ATTR_CONTEXT_GGXF, root)
            if self.validator().validateRootAttributes(metadata, context="GGXF"):
                ggxf = GGXF(metadata)
                for groupname, ncgroup in root.groups.items():
                    self.loadGroup(ggxf, groupname, ncgroup)
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
        if "groupParameters" in metadata and type(metadata["groupParameters"]) == str:
            metadata["groupParameters"] = [metadata["groupParameters"]]
        if not self.validator().validateGroupAttributes(metadata, context=context):
            return
        group = Group(ggxf, groupname, metadata)
        for gridname, ncgrid in ncgroup.groups.items():
            self.loadGrid(group, gridname, ncgrid)
        ggxf.addGroup(group)

    def loadGrid(self, group, gridname, ncgrid, parent=None):
        self._logger.debug(f"Loading grid {gridname}")
        context = f"{group.name()} {gridname}"
        metadata = self.loadMetadata(NETCDF_ATTR_CONTEXT_GRID, ncgrid)
        if self.validator().validateGridAttributes(metadata, context=context):
            try:
                data = np.array(ncgrid[NETCDF_VAR_GRIDDATA])
            except Exception as ex:
                self.error("Cannot load data for grid {gridname}: {ex}")
                return
            grid = Grid(group, gridname, metadata, data)
            for gridname, ncsubgrid in ncgrid.groups.items():
                self.loadGrid(group, gridname, ncsubgrid, grid)
            if parent:
                parent.addGrid(grid)
            else:
                group.addGrid(grid)

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
                    result = {}
                    for field in fields:
                        fval = v[field]
                        if fval.dtype.kind == "f" and fval == np.finfo(fval.dtype).min:
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


class Writer(BaseWriter):
    @staticmethod
    def Write(ggxf, ggxf_file, options=None):
        writer = Writer(options)
        writer.write(ggxf, ggxf_file)

    def __init__(self, options=None):
        BaseWriter.__init__(self, options)
        self._logger = logging.getLogger("GGXF.NetCdfWriter")

    def write(self, ggxf, netcdf4_file: str):
        self._useCompoundTypes = self.getBoolOption(
            NETCDF_OPTION_USE_COMPOUND_TYPE, False
        )
        self._useSnakeCase = self.getBoolOption(
            NETCDF_OPTION_USE_SNAKE_CASE_ATTRIBUTES, False
        )
        # Not currently implemented.
        if self._useCompoundTypes:
            self._logger.warning("Using NetCDF4 compound types (experimental)")
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

        self._logger.debug(f"Saving NetCDF4 grid as {netcdf4_file}")
        if os.path.isfile(netcdf4_file):
            os.remove(netcdf4_file)
        root = netCDF4.Dataset(netcdf4_file, "w", format="NETCDF4")
        self.saveGgxfNetCdf4(root, ggxf)
        root.close()
        if self.getBoolOption(NETCDF_OPTION_WRITE_CDL) or self.getBoolOption(
            NETCDF_OPTION_WRITE_CDL_HEADER
        ):
            root = netCDF4.Dataset(netcdf4_file, "r", format="NETCDF4")
            cdl_file = os.path.splitext(netcdf4_file)[0] + ".cdl"
            data = not self.getBoolOption(NETCDF_OPTION_WRITE_CDL_HEADER)
            root.tocdl(data=data, outfile=cdl_file)

    def saveGgxfNetCdf4(self, root, ggxf):
        nctypes = {}

        # NetCDF compound types
        exclude = [GGXF_ATTR_GGXF_GROUPS, GGXF_ATTR_GRID_DATA]
        converted = {}
        if self._useCompoundTypes:
            # This functionality was lost when refactoring GGXF into multiple modules
            # It was split between creating the compound type in the root group and
            # the variable in the GGXF group in saveGroupNetCdf4.  The code has been
            # moved here as parameters in GGXF are now in the root group.
            #
            # However this isn't working yet.  This implementation is using a variable
            # to hold parameters, but the NetCDF data model implies that they can be held
            # in an attribute.  However this hasn't been tested yet with the python API.
            paramtype = np.dtype(
                [
                    ("parameterName", "S32"),
                    ("unitName", "S16"),
                    ("unitSiRatio", self._dtype),
                    ("parameterMinimumValue", self._dtype),
                    ("parameterMaximumValue", self._dtype),
                    ("noDataFlag", self._dtype),
                ]
            )
            ncparamtype = root.createCompoundType(paramtype, "ggxfParameterType")
            parameters = ggxf.parameters()
            typeinfo = np.finfo(self._dtype)
            paramdata = [
                (
                    p.name(),
                    p.unit(),
                    p.siratio(),
                    p.minvalue() or typeinfo.min,
                    p.maxvalue() or typeinfo.min,
                    p.nodataflag() or typeinfo.min,
                )
                for p in parameters
            ]
            paramdata = np.array(paramdata, dtype=paramtype)
            converted[GGXF_ATTR_PARAMETERS] = paramdata
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

        cdfgroup.createDimension(NETCDF_DIMENSION_NPARAM, nparam)

        self.saveNetCdf4MetdataDot(
            NETCDF_ATTR_CONTEXT_GROUP, cdfgroup, group.metadata(), exclude=exclude
        )

        # Store each of the grids
        grids = group.grids()
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
            #            GRID_ATTR_AFFINE_COEFFS,
        ]

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
        self.saveNetCdf4MetdataDot(
            NETCDF_ATTR_CONTEXT_GRID, cdfgrid, metadata, exclude=exclude
        )

        # Support for nested grid possibility
        for subgrid in grid.subgrids():
            self.saveGridNetCdf4(cdfgrid, subgrid, nctypes, nparam)

    def saveNetCdf4Attr(self, context: str, dataset: netCDF4.Dataset, name: str, value):
        if name == GGXF_ATTR_GGXF_VERSION:
            name = NETCDF_CONVENTIONS_ATTRIBUTE
            value = NETCDF_CONVENTIONS_VALUE.replace("{ggxfVersion}", value)
        elif context == NETCDF_ATTR_CONTEXT_GGXF and name in ACDD_AttributeMapping:
            name = ACDD_AttributeMapping[name]
        elif self._useSnakeCase:
            name = _snakeCase(name)
        dataset.setncattr(name, value)

    def saveNetCdf4MetdataDot(
        self,
        context: str,
        dataset: netCDF4.Dataset,
        entity,
        name: str = "",
        exclude=[],
        converted={},
        base: int = 1,
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
                raise RuntimeError(f"Cannot save {name}: {ex}")
