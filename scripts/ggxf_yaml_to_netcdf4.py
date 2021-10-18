#!/usr/bin/python3
import yaml
import argparse
import json
import netCDF4
import numpy as np

import os
import os.path
import logging
from collections import namedtuple
from typing import Any
import re

logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)


def main():
    parser = argparse.ArgumentParser(
        "Convert a YAML GGXF specification to a NetCDF4 file",
        epilog='This is a test implementation to evaluate encoding options - the output is not necessarily an "authoritative" GGXF file',
    )
    parser.add_argument("ggxf_yaml_file", help="Name of YAML GGXF file to load")
    parser.add_argument("netcdf4_file", help="NetCDF4 file to create")
    parser.add_argument(
        "-g", "--grid-directory", help="Directory to search for grid files"
    )
    parser.add_argument(
        "-m",
        "--metadata-style",
        choices=GGXF.MetadataStyle,
        help="Style for encoding metadata",
    )
    parser.add_argument(
        "-c",
        "--use-compound-types",
        action="store_true",
        help="Use NetCDF compound types for supported objects (very limited implementation)",
    )
    parser.add_argument(
        "-d", "--dump-cdl", action="store_true", help="Create CDL dump of NetCDF file"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="More verbose output"
    )
    # parser.add_argument(
    #     "-s",
    #     "--simplify-1param-grid",
    #     action="store_true",
    #     help="Drop nparam dimension from grids where nparam=1",
    # )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    yaml_file = args.ggxf_yaml_file
    netcdf4_file = args.netcdf4_file

    options = {}
    if args.grid_directory:
        options["grid_directory"] = args.grid_directory
    if args.metadata_style:
        options["metadata_style"] = args.metadata_style
    options["use_compound_types"] = args.use_compound_types
    # options["simplify_1param_grid"] = args.simplify_1param_grid

    ggxf = GGXF(yaml_file, options=options)
    ggxf.save(netcdf4_file, cdl=args.dump_cdl)


class Error(RuntimeError):
    pass


class SchemaError(Error):
    pass


class GGXF:

    RecordType = namedtuple("RecordType", "dtype netcdfType")
    MetadataStyle = ["dot0", "dot1", "json"]

    def __init__(self, yaml_file: str = None, options: dict = None):
        self._data = None
        self._filename = None
        self._logger = logging.getLogger("GGXF")
        self._options = options or {}
        metastyle = options.get("metadata_style", "dot0")
        if metastyle == "json":
            logging.debug("Using JSON metadata format")
            metafunc = lambda dataset, entity, exclude: self._saveNetCdf4MetdataJson(
                dataset, entity, exclude=exclude
            )
        elif metastyle == "dot1":
            logging.debug('Using base 1 "dot" format metadata')
            metafunc = lambda dataset, entity, exclude: self._saveNetCdf4MetdataDot(
                dataset, entity, exclude=exclude, base=1
            )
        else:  # Default is dot0, also used with cdf4 compound types
            logging.debug('Using base 0 "dot" format metadata')
            metafunc = lambda dataset, entity, exclude: self._saveNetCdf4MetdataDot(
                dataset, entity, exclude=exclude, base=0
            )
        self._useCompoundTypes = options.get("use_compound_types", False)
        self._simplify1ParamGrids = options.get("simplify_param_grids", False)
        self._saveMetadata = metafunc
        if yaml_file:
            self.loadYaml(yaml_file)

    def loadYaml(self, yaml_file: str) -> None:
        if not os.path.isfile(yaml_file):
            raise Error(f"{yaml_file} does not exist or is not a file")
        try:
            self._logger.debug(f"Loading YAML {yaml_file}")
            self._data = yaml.load(open(yaml_file).read(), Loader=yaml.SafeLoader)
            self._filename = yaml_file
        except:
            raise Error(f"Cannot load YAML file {yaml_file}")
        self.validate()
        self.loadGrids()

    def loadGrids(self) -> None:
        startdir = os.getcwd()
        griddir = self._options.get("grid_directory", startdir)
        dirset = False
        try:
            for group in self._data["groups"]:
                group["_root"] = self._data
                gridlist = list(group["grids"])
                while gridlist:
                    grid = gridlist.pop(0)
                    gridlist.extend(grid.get("grids", []))
                    grid["affineCoeffs"] = [float(c) for c in grid["affineCoeffs"]]
                    grid["_group"] = group
                    if "gridData" in grid:
                        grid["gridData"] = np.array(grid["gridData"])
                    elif "gridDataSource" in grid:
                        from osgeo import gdal

                        if not dirset:
                            self._logger.debug(
                                f"Changing directory to {griddir} to load grids"
                            )
                            os.chdir(griddir)
                            dirset = True
                        source = grid.pop("gridDataSource")
                        self._logger.debug(f"Loading {source}")
                        dataset = gdal.Open(source)
                        gridData = dataset.ReadAsArray()
                        gridData = np.moveaxis(gridData, 0, 2)
                        grid["gridData"] = gridData
                        self._logger.debug(
                            f"Loaded grid with dimension {gridData.shape}"
                        )
                        # Get grid metadata to validate against YAML...
        finally:
            os.chdir(startdir)

    def validate(self) -> None:
        """
        Not implemented: Currently have a placeholder implementation pending a genuine schema implementation
        """
        data = self._data
        if "groups" not in data or not isinstance(data["groups"], list):
            raise SchemaError("groups not defined or not a list")
        for igroup, group in enumerate(data["groups"]):
            if "groupName" not in group:
                raise SchemaError(f"groupName not defined in groups[{igroup}]")
            if "grids" not in group or not isinstance(group["grids"], list):
                raise SchemaError(
                    f"grids not defined or not a list in group {group['groupName']}"
                )

    def save(self, netcdf4_file: str, cdl: bool = False):
        self._logger.debug(f"Saving NetCDF4 grid as {netcdf4_file}")
        if os.path.isfile(netcdf4_file):
            os.remove(netcdf4_file)
        root = netCDF4.Dataset(netcdf4_file, "w", format="NETCDF4")
        self._saveNetCdf4(root)
        root.close()
        if cdl:
            root = netCDF4.Dataset(netcdf4_file, "r", format="NETCDF4")
            cdl_file = os.path.splitext(netcdf4_file)[0] + ".cdl"
            root.tocdl(data=True, outfile=cdl_file)

    def _saveNetCdf4(self, root):
        data = self._data
        nctypes = {}

        # Common dimensions - affine now managed as attribute rather than variable
        # root.createDimension("affine",6)
        # Tried using unlimited dimension for parameter list.  Cause ncdump 4.7.3 to crash.
        # root.createDimension("parameter",None)

        # NetCDF compound types
        if self._useCompoundTypes:
            paramtype = np.dtype(
                [("parameterName", "S32"), ("unit", "S16"), ("unitSiRatio", np.float64)]
            )
            ncparamtype = root.createCompoundType(paramtype, "ggxfParameterType")
            nctypes["ggxfParameterType"] = GGXF.RecordType(paramtype, ncparamtype)

        self._saveMetadata(root, data, ["groups"])

        # Store each of the groups
        for group in data["groups"]:
            self._saveGroupNetCdf4(root, group, nctypes)

    def _saveGroupNetCdf4(self, root: netCDF4.Dataset, group: dict, nctypes: dict):
        name = group.get("groupName")
        cdfgroup = root.createGroup(name)
        exclude = ["groupName", "grids"]

        # Store group attributes
        cdfgroup.setncatts({"remark": group.get("remark", "")})
        # Store the parameters saved as array of compound type
        parameters = group.get("parameters", [])
        nparam = len(parameters)

        cdfgroup.createDimension("nParam", nparam)
        if self._useCompoundTypes:
            paramdata = [
                (p["parameterName"], p["unit"], p["unitSiRatio"]) for p in parameters
            ]
            paramtype = nctypes["ggxfParameterType"]
            paramdata = np.array(paramdata, dtype=paramtype.dtype)
            paramvar = cdfgroup.createVariable(
                "parameters", paramtype.netcdfType, "nParam"
            )
            paramvar[:] = paramdata
            exclude.append("parameters")

        self._saveMetadata(cdfgroup, group, exclude)

        # Store each of the grids
        for grid in group["grids"]:
            self._saveGridNetCdf4(cdfgroup, grid, nctypes, nparam)

    def _saveGridNetCdf4(
        self, cdfgroup: netCDF4.Group, grid: dict, nctypes: dict, nparam: int
    ):
        name = grid.get("gridName")
        cdfgrid = cdfgroup.createGroup(name)
        exclude = ["gridName", "grids", "gridData", "gridDataSource", "affineCoeffs"]

        # Store group attributes
        cdfgrid.setncatts({"affineCoeffs": grid["affineCoeffs"]})

        # Store the grid metadata
        # affinevar=cdfgrid.createVariable('affineCoeffs',np.float64,'affine')
        # self._logger.debug(f"Filling affineCoeffs {affinevar.shape} {affinevar.datatype} from {grid['affineCoeffs']}")
        # affinevar[:]=np.array(grid['affineCoeffs'])

        ncol = grid["iNodeMaximum"] + 1
        nrow = grid["jNodeMaximum"] + 1
        cdfgrid.createDimension("nCol", ncol)
        cdfgrid.createDimension("nRow", nrow)
        dimensions = (nrow, ncol, nparam)

        # Store the grid data
        datavar = cdfgrid.createVariable("data", np.float64, ["nRow", "nCol", "nParam"])
        data = grid["gridData"]
        if data.shape != dimensions:
            self._logger.debug(f"Reshaping grid from {data.shape} to {dimensions}")
            data = data.reshape(dimensions)
        datavar[:, :, :] = data

        self._saveMetadata(cdfgrid, grid, exclude)

        # Support for nested grid possibility
        for subgrid in grid.get("grids", []):
            self._saveGridNetCdf4(cdfgrid, subgrid, nctypes, nparam)

    def _saveNetCdf4MetdataDot(
        self,
        dataset: netCDF4.Dataset,
        entity: Any,
        name: str = "",
        exclude=[],
        base: int = 0,
    ) -> None:
        if type(entity) == dict:
            if name != "":
                name = name + "."
            for key, value in entity.items():
                if key not in exclude and not key.startswith("_"):
                    self._saveNetCdf4MetdataDot(dataset, value, name + key, base=base)
        elif type(entity) == list:
            count = int(len(entity))
            self._saveNetCdf4MetdataDot(dataset, count, name + ".count")
            for ival, value in enumerate(entity):
                self._saveNetCdf4MetdataDot(dataset, value, name + f".{ival+base}")
        else:
            try:
                dataset.setncattr(name, entity)
            except Exception as ex:
                raise RuntimeError(f"Cannot save {name}: {ex}")

    def _saveNetCdf4MetdataJson(
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


if __name__ == "__main__":
    main()
