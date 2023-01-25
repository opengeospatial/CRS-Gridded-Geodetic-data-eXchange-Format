from osgeo import gdal
import os
import os.path
import json
import yaml
import re
from urllib import request
import numpy as np
import logging
from .Constants import *
from .GGXF_Types import *
from .GridLoader.GDAL import GdalDatasetMapping, GDAL_SOURCE_ATTR, MetadataTemplate
from .YAML import Util, SOURCE_ATTR_SOURCE_TYPE


EpsgApiUrlEnv = "EPSG_API_URL"
EpsgCacheFileEnv = "EPSG_CACHE_FILE"
GdalDriverConfigFileEnv = "GDAL_DRIVER_PARAMETER_CONFIG"

EpsgApiUrl = os.environ.get(
    EpsgApiUrlEnv,
    "https://apps.epsg.org/api/v1/CoordRefSystem/{crdsysid}/export/?format=wkt",
)
EpsgApiTimeoutSeconds = 30
EpsgCacheFile = os.environ.get(EpsgCacheFileEnv)
GdalDriverConfigFile = os.environ.get(
    GdalDriverConfigFileEnv,
    os.path.join(os.path.dirname(__file__), "gdal_driver_parameters.yaml"),
)


CrsAttributes = (
    GGXF_ATTR_INTERPOLATION_CRS_WKT,
    GGXF_ATTR_SOURCE_CRS_WKT,
    GGXF_ATTR_TARGET_CRS_WKT,
)


class GdalImportError(Exception):
    pass


class GdalImporter:
    @staticmethod
    def AddImporterArguments(parser):
        parser.add_argument(
            "yaml_file", help="Output YAML file - GGXF or metadata template"
        )
        parser.add_argument(
            "grid_file",
            nargs="?",
            help="Grid file to import (if not supplied just write a template)",
        )
        parser.add_argument(
            "-m",
            "--metadata-file",
            action="append",
            help="Input file of metadata (may be repeated)",
        )
        parser.add_argument("-c", "--content-type", help="GGXF content type of grid")
        parser.add_argument(
            "-a",
            "--attribute",
            action="append",
            help="GGXF file attribute written as attribute=value",
        )
        parser.add_argument(
            "-p",
            "--include-placeholders",
            action="store_true",
            help="Include placeholder metadata in output GGXF YAML",
        )
        parser.add_argument(
            "-w",
            "--write-template",
            action="store_true",
            help="Write metadata template to YAML file instead of GGXF",
        )
        parser.add_argument(
            "-e",
            "--epsg-codes",
            help="Interpolation, source, and target EPSG codes separated by /",
        )
        parser.add_argument(
            "--ignore-errors",
            action="store_true",
            help="Less rigorous checking of GGXF YAML file",
        )

    @staticmethod
    def ProcessImporterArguments(args):
        yaml_file = args.yaml_file
        if not yaml_file.endswith(".yaml"):
            raise GdalImportError(f'YAML filename ({yaml_file}) must end with ".yaml"')

        attrargs = args.attribute or []
        attributes = {}
        for attr in attrargs:
            match = re.match(r"(\w+)\=(.+)", attr)
            if not match:
                raise GdalImportError(
                    f'--attribute parameter {attr} must be formatted as "attribute=value"'
                )
            attributes[match.group(1)] = match.group(2)

        GdalImporter.Import(
            args.yaml_file,
            args.grid_file,
            args.metadata_file,
            epsg_codes=args.epsg_codes,
            attributes=attributes,
            write_template=args.write_template,
            content_type=args.content_type,
            include_placeholders=args.include_placeholders,
            ignore_errors=args.ignore_errors,
        )

    @staticmethod
    def Import(
        yaml_file,
        grid_file=None,
        metadata_files=None,
        attributes=None,
        epsg_codes=None,
        write_template=False,
        content_type=None,
        include_placeholders=False,
        ignore_errors=False,
    ):
        # Build up the metadata that will form the template.  This will
        # end up either creating a new metadata file, or providing the
        # metadata for the GGXF YAML.

        # Load the metadata file(s) to the default template.  The default template
        # just has prompts for each attribute, don't copy these into the compiled
        # template

        template = MetadataTemplate.copy()
        for metafile in metadata_files or []:
            if not os.path.exists(metafile):
                raise GdalImportError(f"Cannot find metadata file {metafile}")
            try:
                with open(metafile) as mfh:
                    metadata = yaml.safe_load(mfh)
                for key, value in metadata.items():
                    if key not in MetadataTemplate or value != MetadataTemplate[key]:
                        template[key] = value

            except Exception as ex:
                raise GdalImportError(
                    f"Unable to read metadata from {metafile} - format error?"
                )

        # Add attributes from command line
        if attributes is not None:
            for key, value in attributes.items():
                if key not in MetadataTemplate:
                    raise GdalImportError(f"Invalid attribute {key} specified")
                template[key] = value

        if epsg_codes is not None:
            codes = epsg_codes.split("/")
            if len(codes) != 3:
                raise GdalImportError(
                    f"epsg_codes must be formatted interpolation_code/source_code/target_code"
                )
            for attr, code in zip(CrsAttributes, codes):
                if not re.match(r"^\d+$", code):
                    raise GdalImportError(f"Invalid epsg_code {code} for {attr}")
                template[attr] = f"EPSG:{code}"

        # Handle content type
        if content_type is not None:
            template[GGXF_ATTR_CONTENT] = content_type

        # If we have a grid file then add the derivable metadata

        if grid_file is not None:
            gdal.UseExceptions()
            try:
                root = gdal.Open(grid_file)
            except Exception as ex:
                raise GdalImportError(f"Error loading {grid_file}: {ex}")

            driverName = root.GetDriver().ShortName
            # Get normallised parameter names
            parameters = []
            for band in range(root.RasterCount):
                rb = root.GetRasterBand(band + 1)
                name = rb.GetDescription()
                name = name.strip()
                name = re.sub(r"[^\w\s].*", "", name)
                name = re.sub(r"\s+(\w)", lambda m: m.group(1).upper(), name.lower())
                name = re.sub(r"\s+", "", name)
                if name == "":
                    name = f"band{band}"
                parameters.append(name)

            if template[GGXF_ATTR_PARAMETERS] == MetadataTemplate[GGXF_ATTR_PARAMETERS]:
                template[GGXF_ATTR_PARAMETERS] = [
                    {
                        PARAM_ATTR_PARAMETER_NAME: name,
                        PARAM_ATTR_UNIT_NAME: "Enter unit name",
                    }
                    for name in parameters
                ]

            # Some drivers have specific metadata configuration (eg ISG is
            # used for geoidHeight).  Get the configuration for the driver of this
            # data set.

            driverConfig = GdalImporter.GetDriverConfiguration(driverName)
            if driverConfig is not None:
                template = {k: driverConfig.get(k, v) for k, v in template.items()}

            # Expand EPSG:id CRS definitions from the template by retrieving CRSWKT
            # from the EPSG API
            for key in CrsAttributes:
                if key in template and template[key] != MetadataTemplate[key]:
                    template[key] = GdalImporter.GetEpsgCrdsysWkt(template[key])

        # Add a default interpolation method
        if GROUP_ATTR_INTERPOLATION_METHOD not in template:
            template[GROUP_ATTR_INTERPOLATION_METHOD] = INTERPOLATION_METHOD_BILINEAR

        # If the user just wants a metadata template, then write it out now and exit
        if write_template or grid_file is None:
            with open(yaml_file, "w") as mfh:
                yaml.safe_dump(template, mfh, sort_keys=False, indent=2, width=256)
            print(f"Dataset metadata template written to {yaml_file}")
            return

        ###########################################################
        # Build the GGXF structure...

        # Validate the content type and parameters

        content_type = template.get(GGXF_ATTR_CONTENT, "")
        if content_type not in ContentTypes:
            raise GdalImportError(f"Invalid content type {content_type} in template")
        contentdef = ContentTypes.get(content_type)

        parameters = template.get(GGXF_ATTR_PARAMETERS, [])
        paramset = set([p.get(PARAM_ATTR_PARAMETER_NAME, "") for p in parameters])
        if paramset not in contentdef.get(ATTRDEF_PARAMETER_SETS, []):
            message = (
                f"Parameters ({','.join(paramset)}) are not valid for {content_type}"
            )
            if ignore_errors:
                logging.warn(message)
            else:
                raise GdalImportError(message)
        paramsets = contentdef[ATTRDEF_PARAMSET_MAP]
        for param in parameters:
            pname = param[PARAM_ATTR_PARAMETER_NAME]
            if PARAM_ATTR_PARAMETER_SET not in param and pname in paramsets:
                param[PARAM_ATTR_PARAMETER_SET] = paramsets[pname]

        # Compile the grids

        rootgrids, gridrange = GdalImporter.CompileGrids(root)

        # Define the GGXF content applicability extent.  The user template can
        # include a placeholder for this which the user can replace with a description.
        #
        # NOTE: This is not safe - currently assumes that interpolation CRS is
        # geographic (east positive) and ordered latitude, longitude.

        extent = {
            GGXF_ATTR_BOUNDING_BOX: {
                GGXF_ATTR_SOUTH_BOUND_LATITUDE: gridrange[0],
                GGXF_ATTR_WEST_BOUND_LONGITUDE: gridrange[1],
                GGXF_ATTR_NORTH_BOUND_LATITUDE: gridrange[2],
                GGXF_ATTR_EAST_BOUND_LONGITUDE: gridrange[3],
            }
        }
        if GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT in template:
            description = template[GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT]
            if (
                isinstance(description, str)
                and description
                != MetadataTemplate[GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT]
            ):
                extent[GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT] = description
        template[GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT] = extent

        # Build the ggxf structure (Currently building manually rather than using GGXF.GGXF object)
        # Start with the parameters that are in the template and are different from the
        # default prompt in the MetadataTemplate

        ggxf = {
            GGXF_ATTR_GGXF_VERSION: GGXF_VERSION_G_G_X_F_1_0,
            GGXF_ATTR_FILENAME: os.path.basename(yaml_file),
        }
        for key, placeholder in MetadataTemplate.items():
            if key not in template:
                continue
            if template[key] != placeholder or include_placeholders:
                ggxf[key] = template[key]

        interpolationMethod = template.get(
            GROUP_ATTR_INTERPOLATION_METHOD, INTERPOLATION_METHOD_BILINEAR
        )

        # Add the GGXF
        ggxf[GGXF_ATTR_GGXF_GROUPS] = [
            {
                GROUP_ATTR_GGXF_GROUP_NAME: os.path.basename(grid_file),
                GROUP_ATTR_INTERPOLATION_METHOD: interpolationMethod,
                GROUP_ATTR_GRIDS: rootgrids,
            }
        ]

        # Write the compiled GGXF object to a YAML file
        GdalImporter.WriteYaml(yaml_file, ggxf)

    @staticmethod
    def CompileGrids(root):
        datasets = [root]
        for fname, name in root.GetSubDatasets():
            subset = gdal.Open(fname)
            datasets.append(subset)

        grids = {}
        parents = {}
        xmin, ymin, xmax, ymax = None, None, None, None

        for dataset in datasets:
            description = dataset.GetDescription()
            meta = dataset.GetMetadata_Dict()
            name = meta.get("SUB_NAME", description)
            parent = meta.get("PARENT", "NONE")
            size, affine = GdalDatasetMapping(dataset)
            if name in grids:
                raise RuntimeError(f"Grid name {name} is duplicated")
            grids[name] = {
                GRID_ATTR_GRID_NAME: name,
                GRID_ATTR_AFFINE_COEFFS: affine,
                GRID_ATTR_I_NODE_COUNT: size[0],
                GRID_ATTR_J_NODE_COUNT: size[1],
                GRID_ATTR_DATA_SOURCE: {
                    SOURCE_ATTR_SOURCE_TYPE: "GDAL",
                    GDAL_SOURCE_ATTR: description,
                },
            }
            if parent != "NONE":
                parents[name] = parent

            # Calculate the grid extents and update for the dataset extent.
            for i in (0, size[0] - 1):
                for j in (0, size[1] - 1):
                    x = np.sum([1, i, j] * affine[:3])
                    y = np.sum([1, i, j] * affine[3:])
                    if xmin is None:
                        xmin = x
                        xmax = x
                        ymin = y
                        ymax = y
                    else:
                        xmin = min(x, xmin)
                        xmax = max(x, xmax)
                        ymin = min(y, ymin)
                        ymax = max(y, ymax)

        # Compile nested grid structure
        rootgrids = []
        for name, grid in grids.items():
            if name not in parents:
                rootgrids.append(grid)
            else:
                pgrid = grids.get(parents[name])
                if pgrid is None:
                    raise GdalImportError(f"Parent grid {parents[name]} not defined")
                if GRID_ATTR_CHILD_GRIDS not in pgrid:
                    pgrid[GRID_ATTR_CHILD_GRIDS] = []
                pgrid[GRID_ATTR_CHILD_GRIDS].append(grid)
        return rootgrids, [float(x) for x in (xmin, ymin, xmax, ymax)]

    @staticmethod
    def GetDriverConfiguration(driverName):
        if not os.path.exists(GdalDriverConfigFile):
            logging.debug(
                f"Cannot open GDAL driver configuration file {GdalDriverConfigFile}"
            )
            return None
        try:
            with open(GdalDriverConfigFile) as dcfg:
                drivers = yaml.safe_load(dcfg)
                if driverName in drivers.keys():  # Use keys to fail if not a dictionary
                    config = drivers[driverName]
                    if GGXF_ATTR_CONTENT not in config.keys():
                        logging.error(
                            f"GDAL configuration for {driverName} in {GdalDriverConfigFile} does not include {GGXF_ATTR_CONTENT}"
                        )
                        return None
                    return config
                else:
                    logging.debug(
                        f"GDAL driver {driverName} not found in {GdalDriverConfigFile}"
                    )
                    return None
        except Exception as ex:
            logging.error(
                f"GDAL driver configuration file {GdalDriverConfigFile} unreadable or incorrectly formatted: {ex}"
            )
        return None

        driverConfig = (os.path.dirname(__file__),)

    @staticmethod
    def WriteYaml(yaml_file, data):
        dumper = yaml.SafeDumper
        dumper.add_representer(np.ndarray, Util.dumpNdArray)
        dumper.add_representer(str, Util.dumpString)
        with open(yaml_file, "w") as yamlh:
            yaml.safe_dump(data, yamlh, indent=2, sort_keys=False)

    @staticmethod
    def GetEpsgCrdsysWkt(crdsysid):
        match = re.match(r"epsg:(\d+)$", crdsysid.lower().strip())
        if not match:
            return crdsysid
        epsgid = match.group(1)
        url = EpsgApiUrl.replace("{crdsysid}", epsgid)
        cache = {}
        cachefile = EpsgCacheFile
        if cachefile is not None:
            try:
                with open(cachefile) as ch:
                    fcache = json.load(ch)
                    if isinstance(fcache, dict):
                        cache = fcache
            except:
                if os.path.exists(cachefile):
                    logging.debug(f"Failed to read JSON dict object from {cachefile}")
                    cachefile = None

        if epsgid not in cache:
            try:

                with request.urlopen(url, timeout=EpsgApiTimeoutSeconds) as response:
                    status = response.getcode()
                    if status != 200:
                        logging.debug(
                            f"Invalid EPSG code {crdsysid} or EPSG API unresponsive"
                        )
                    else:
                        cache[epsgid] = response.read().decode("utf8")
            except Exception as ex:
                logging.warn(f"Unable to lookup WKT for {epsgid} from {url}")

        if cachefile is not None:
            try:
                with open(cachefile, "w") as ch:
                    json.dump(cache, ch, indent=2)
            except:
                pass
        return cache.get(epsgid, crdsysid)


if __name__ == "__main__":
    import argparse
    import os.path

    parser = argparse.ArgumentParser(
        description="Import GDAL compatible grid file to GGXF YAML format"
    )
    GdalImporter.AddImporterArguments(parser)
    args = parser.parse_args()
    GdalImporter.ProcessImporterArguments(args)
