# Overview

This directory contains experimental python 3.8+ script to test NetCDF4 encoding options for a GGXF.
These scripts are intended for experimenting with the GGXF format - they are not "production ready".  

# Scripts

This directory contains three scripts to support generating and experimenting with GGXF format files.

* ggxf.py - converts GGXF YAML <-> NetCDF, Calculate values from GGXF dataset, dumps GGXF summary data
* deformation_model_to_ggxf_yaml.py - compiles a GGXF YAML file from a JSON/GeoTIFF encoded deformation model

## ggxf.py script

This is the main utility built for processing GGXF files. It has four basic functions:

* ggxf.py convert - Converts files between YAML and NetCDF GGXF formats
* ggxf.py describe - Briefly describes the content of a GGXF file
* ggxf.py calculate - Evaluates the parameters of the GGXF file at CSV file of test locations.  (Note this does not apply the coordinate operation, just calculates the values it would use)
* ggxf.py import - Imports data from a [GDAL supported](https://gdal.org/drivers/raster/index.html)  grid file to a GGXF YAML.  This may include placeholders for missing attributes, or maybe supplied attributes from a YAML template.

Each of these options includes some online help available with the --help option (eg ggxf.py import --help).

### Convert arguments

```
usage: ggxf convert [-h] [-n option=value] [-y option=value] [-g] [-v]
                    input_ggxf_file output_ggxf_file

Convert between YAML and NetCDF formats

positional arguments:
  input_ggxf_file       Input GGXF file, either .yaml or .ggxf
  output_ggxf_file      Output GGXF file, either .yaml or .ggxf

options:
  -h, --help            show this help message and exit
  -n option=value, --netcdf4-options option=value
                        Format options for NetCDF4 files
  -y option=value, --yaml-options option=value
                        Format options for YAML files
  -g, --debug           Generate debugging output
  -v, --verbose         More verbose output

Format options for reading a YAML GGXF file can be

  "grid-directory" Base directory (relative to YAML file) used for grid files
  "check-datasource-affine-coeffs" Compare affine coeffs from data source with those defined in YAML (true or false)
  

Format options for reading a NetCDF4 GGXF file can be

  "grid_dtype" Specifies the data type used for the grid (float64, float32, int32, int16)

  When reading a NetCDF file the default floating point is float64 to avoid rounding issues.

Format options for writing a YAML GGXF file can be:

  "grid-directory" Base directory (relative to YAML file) used for grid files
  "write-csv-grids" Write grids to external ggxf-csv grids (true or false, default true)
  "write-csv-node-coordinates" Write node coordinates in CSV (true or false, default true)
  "write-headers-only" Write headers only - omit the grid data

Format options for writing a NetCDF4 GGXF file can be:

  "grid_dtype" Specifies the data type in the NetCDF file (float64, float32, int32, int16)
  "write-cdl" Generate an output CDL file as well as a NetCDF file (full, header, or none)
  "packing-precision" Specifies integer packing using specified number of decimal places

  If packing-precision is specified then grid_dtype is ignored and integer packing
  is attempted.  If an integer data type is specified then the data will be scaled to fill the range available
  with the integer type.  If neither is specified float32 is used.


```

### Describe arguments

```
Describe a GGXF file

positional arguments:
  input_ggxf_file       Input GGXF file, either .yaml or .ggxf

options:
  -h, --help            show this help message and exit
  -n option=value, --netcdf4-options option=value
                        Format options for NetCDF4 files
  -y option=value, --yaml-options option=value
                        Format options for YAML files
  -c filename, --csv-grid-summary filename
                        Write a CSV file containing a summary of grids
  -d #, --coordinate-decimal-places #
                        Number of decimal places for coordinates
  -p #, --parameter-decimal-places #
                        Number of decimal places for values in summary file
  -g, --debug           Generate debugging output
  -v, --verbose         More verbose output

Format options for reading a YAML GGXF file can be

  "grid-directory" Base directory (relative to YAML file) used for grid files
  "check-datasource-affine-coeffs" Compare affine coeffs from data source with those defined in YAML (true or false)
  

Format options for reading a NetCDF4 GGXF file can be

  "grid_dtype" Specifies the data type used for the grid (float64, float32, int32, int16)

  When reading a NetCDF file the default floating point is float64 to avoid rounding issues.
```

### Calculate arguments

```
usage: ggxf calculate [-h] [-n option=value] [-y option=value] [-d #]
                      [-e ####.#] [-b ####.#] [-g] [-v]
                      input_ggxf_file filename filename

Calculate parameters from a GGXF file

positional arguments:
  input_ggxf_file       Input GGXF file, either .yaml or .ggxf
  filename              Input CSV file of point coordinates
  filename              Results CSV file

options:
  -h, --help            show this help message and exit
  -n option=value, --netcdf4-options option=value
                        Format options for NetCDF4 files
  -y option=value, --yaml-options option=value
                        Format options for YAML files
  -d #, --csv-decimal-places #
                        Number of decimal places for CSV calculated values
  -e ####.#, --epoch ####.#
                        Epoch in years at which to calculate GGXF
  -b ####.#, --base-epoch ####.#
                        Base epoch in years for calculating change between epochs
  -g, --debug           Generate debugging output
  -v, --verbose         More verbose output

The input CSV file must have a header row of field names.  The input
coordinate are in columns nodeLatitude, nodeLongitude, or if the 
interpolationCrs is a projection CRS then nodeEasting, nodeNorthing.

Format options for reading a YAML GGXF file can be

  "grid-directory" Base directory (relative to YAML file) used for grid files
  "check-datasource-affine-coeffs" Compare affine coeffs from data source with those defined in YAML (true or false)
  

Format options for reading a NetCDF4 GGXF file can be

  "grid_dtype" Specifies the data type used for the grid (float64, float32, int32, int16)

  When reading a NetCDF file the default floating point is float64 to avoid rounding issues.

```

### Import arguments

```
usage: ggxf import [-h] [-m METADATA_FILE] [-c CONTENT_TYPE] [-a ATTRIBUTE]
                   [-w] [-p] [--ignore-errors] [-g] [-v]
                   yaml_file [grid_file]

Import GDAL supported grid formats to GGXF

positional arguments:
  yaml_file             Output YAML file - GGXF or metadata template
  grid_file             Grid file to import (if not supplied just write a template)

options:
  -h, --help            show this help message and exit
  -m METADATA_FILE, --metadata-file METADATA_FILE
                        Input file of metadata (may be repeated)
  -c CONTENT_TYPE, --content-type CONTENT_TYPE
                        GGXF content type of grid
  -a ATTRIBUTE, --attribute ATTRIBUTE
                        GGXF file attribute written as attribute=value
  -w, --write-template  Write metadata template to YAML file instead of GGXF
  -p, --include-placeholders
                        Include placeholder metadata in output GGXF YAML
  --ignore-errors       Less rigorous checking of GGXF YAML file
  -g, --debug           Generate debugging output
  -v, --verbose         More verbose output

Basic usage:
    ggxf import meta_template.yaml
        Creates a metadata template file meta_template.yaml

    ggxf import -w meta_file.yaml grid_file
        Includes metadata template including attributes from grid file.

    ggxf import ggxf_file.yaml grid_file
        Creates a GGXF file to import data from the grid file.

    ggxf convert ggxf_file.yaml ggxf_file.ggxf
        Convert the YAML GGXF file to NetCDF

The import may include one or more input template files using
the -m option.  Each of these will be used in turn to update attributes 
in the output YAML file. After these are applied any attributes specified
by -a will be applied.  If -p is specified then attributes not explicitly 
set will be included in the ggxf_file.yaml with placeholder values, otherwise
they are omitted.

Some GDAL drivers have specific content types and parameter definitions (eg
NTv2).  These may be configured in a YAML file identified by an environment
variable GDAL_DRIVER_PARAMETER_CONFIG.

The interpolation, source, and target CRS may be specified as EPSG:nnnn.  The EPSG API will be queried to retrieve the full CRS WKT specification.  The WKT strings can be cached in a JSON file specified by environment variable EPSG_CACHE_FILE.

```

## GGXF module

The GGXF directory contains the modules that implement  for reading and writing GGXF files in YAML and NetCDF format, and for calculating values from the GGXF grids.  It also supports extracting some summary information from GGXF files, in particular a summary of the grids in the file.  

This code has evolved alongside the specification and contains several options for alternative GGXF format choices that have been experimented.  Its main purpose has been to build example GGXF files and demonstrate the feasibility and impact of implementation choices.

* Reading and writing a NetCDF4 GGXF file
* Reading and writing a YAML format GGXF file
* Calculating the GGXF grid value at a set of points in a CSV formatted file (with columns X and Y corresponding to the first and second ordinates of the interpolation coordinate system).  If there is more than one group in the GGXF file it calculates values for every group.  This currently does not handle deformation models or time functions and only implements bilinear interpolation.
* Dumping a single grid from the GGXF file as a CSV file of coordinates and values with one row for each grid node (mainly for checking the grid layout/affine transformation is correct)
* Adding deformation model time functions and calculating the deformation model
* Implementing biquadratic and bicubic interpolation functions
* Some parameter and content type validation.

### deformation_model_to_ggxf_yaml.py

An experimental script to convert a JSON/GeoTIFF format deformation file to GGXF YAML.  Under development.
