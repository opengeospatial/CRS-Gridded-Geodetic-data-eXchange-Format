# Overview

This directory contains experimental python 3.8+ script to test NetCDF4 encoding options for a GGXF.
These script are intended for experimenting with the GGXF format - they are not "production ready".  

## ggxf_yaml_to_netcdf4.py

This script converts a YAML format GGXF file to a NetCDF4 file.  This includes some alternative
encoding options for the NetCDF4 file as the final format is under discussion.  It is intended that
the functionality of this script is migrated into GGXF.py, described below.

### Usage

``` text
Usage: Convert a YAML GGXF specification to a NetCDF4 file [-h]
                                                           [-g GRID_DIRECTORY]
                                                           [-m {dot0,dot1,json}]
                                                           [-c] [-d] [-v]
                                                           ggxf_yaml_file
                                                           netcdf4_file

positional arguments:
  ggxf_yaml_file        Name of YAML GGXF file to load
  netcdf4_file          NetCDF4 file to create

optional arguments:
  -h, --help            show this help message and exit
  -g GRID_DIRECTORY, --grid-directory GRID_DIRECTORY
                        Directory to search for grid files
  -m {dot0,dot1,json}, --metadata-style {dot0,dot1,json}
                        Style for encoding metadata
  -c, --use-compound-types
                        Use NetCDF compound types for supported objects (very
                        limited implementation)
  -d, --dump-cdl        Create CDL dump of NetCDF file
  -v, --verbose         More verbose output

This is a test implementation to evaluate encoding options - the output is not
necessarily an "authoritative" GGXF file

```

Currently this has provided three metadata options.  

The default "dot0" style uses a dot naming convention for attributes to encode the data structure, for example "contentApplicabilityExtent.boundingBox.southBoundLatitude".  Lists are encoded with a "*attribute*.count" attribute holding the number of elements in the list, followed by "*attribute*.0", "*attribute*.1".  

The "dot1" style is identical to "dot0" except that lists attributes are 1 based rather than 0 based.

The "json" style encodes all GGXF attributes into a JSON formated string stored in a NetCDF "metadata"

This implementation also includes a very limited test of using NetCDF4 compound data types to represent attributes.  Currently only parameter definitions supported.

### Installation

This script requires installing python3 modules netCDF4, pyyaml, and numpy.  If grids are defined using a dataSource attribute then the gdal module is also required.  

### Issues

* Integer attributes (such as list counts) are encoded with data type long long, for example "3LL".  This doesn't affect usage, but could impact on decoding with other tools.  This may be a constraint of the netCDF python library - to be investigated.

* Implementation using NetCDF4 compound types is very limited.  If this option is preferred for some or all attributes this will need to be addressed.

* Currently grid data are encoded as a (nrow,ncol,nparam) dimensioned variable.  One other option that has been proposed is using a separate (nrow,ncol) variable for each parameter - this is not provided as an option here.  Another option that could be implemented for grids with just one parameter is to collapse (nrow,ncol,1) dimension arrays to (nrow,ncol) arrays.

* A partial JSON option implementation might be useful where genuine metadata (ie data about the data used for discovery rather than attributes such affineCoeffs that are required to calculate the grid) are encoded into a JSON formatted metadata attribute rather than encoding as CDF attributes, particularly if this matches a JSON format used for discovery/search.

* Implementation - this is currently implemented as a single python script.  Once the NetCDF implementation is decided it will be better implemented with as a GGXF module with options for reading and writing both YAML and NetCDF representation, as well as schema validation.  

## GGXF.py

This is under development.  It is intended as a prototype python module for handling GGXF files.  Currently it has capabilities for:

* Reading and writing a NetCDF4 GGXF file
* Reading and writing a YAML format GGXF file
* Calculating the GGXF grid value at a set of points in a CSV formatted file (with columns X and Y corresponding to the first and second ordinates of the interpolation coordinate system).  If there is more than one group in the GGXF file it calculates values for every group.  This currently does not handle deformation models or time functions and only implements bilinear interpolation.
* Dumping a single grid from the GGXF file as a CSV file of coordinates and values with one row for each grid node (mainly for checking the grid layout/affine transformation is correct)
* Adding deformation model time functions and calculating the deformation model
* Implementing biquadratic and bicubic interpolation functions

Intended development includes:

* Checking the GGXF content attribute to ensure the content type is correct and group parameters match the content type.
* Handling of summation of uncertainty for deformation.  RMS?
* Support for "no-data" value
* ? Handling of covariance for deformation
* ? Support for non-GGXF data in grid
* ? Lazy loading of grid data
* Test suite

If it is to be adapted for production use it will also require

* A lot of documentation
* Packaging

GGXF.py includes a basic command line application for testing.  The options provided by this will change as the program is developed.  To see the command line usage run the command

``` sh
python3 GGXF.py -h
```

``` text

usage: Read, save, calculate a GGXF file [-h] [-o OUTPUT_GGXF_FILE]
                                         [-n NETCDF4_OPTION] [-y YAML_OPTION]
                                         [-c COORD_CSV_FILE]
                                         [--output-csv-file OUTPUT_CSV_FILE]
                                         [--csv-decimal-places CSV_DECIMAL_PLACES]
                                         [--csv-summary CSV_SUMMARY]
                                         [--json-summary JSON_SUMMARY]
                                         [--list-grids]
                                         [--dump-grid DUMP_GRID DUMP_GRID]
                                         [-v]
                                         ggxf_file

positional arguments:
  ggxf_file             Name of GGXF file to load - .yaml for YAML format

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_GGXF_FILE, --output-ggxf-file OUTPUT_GGXF_FILE
                        Save GGXF to file - .yaml for YAML format
  -n NETCDF4_OPTION, --netcdf4-option NETCDF4_OPTION
                        option=value for NetCDF4 files (see below for options)
  -y YAML_OPTION, --yaml-option YAML_OPTION
                        option=value for YAML files (see below for options)
  -c COORD_CSV_FILE, --coord-csv-file COORD_CSV_FILE
                        CSV file of points to calculate - assumes column headers with X, Y columns
  --output-csv-file OUTPUT_CSV_FILE
                        CSV file to convert - assumes column headers with X, Y columns (default based on input)
  --csv-decimal-places CSV_DECIMAL_PLACES
                        Number of decimal places for CSV calculated values
  --csv-summary CSV_SUMMARY
                        Write a grid summary to the named CSV file
  --json-summary JSON_SUMMARY
                        Write a (somewhat arbitrary) JSON summary to the named file
  --list-grids          Print a list of grids
  --dump-grid DUMP_GRID DUMP_GRID
                        Number of grid and file name to dump grid (use --list-grids to get grid numbers)
  -v, --verbose         More verbose output

This is a proof of concept implementation to evaluate encoding options.
The output is not necessarily an "authoritative" GGXF file

The following options apply to NetCDF input (I) and output (O):

  "use_nested_grids" (O) Generate NetCDF with nested grid definition (true or false, default true)
  "simplify_1param_grids" (O) Grids with just one parameter are created with just 2 dimensions (default false)
  "write_cdl" (O) Generate an output CDL file as well as a NetCDF file (default false)
  "use_compound_types" (O) Use compound types (very limited test implementation) (default false)

The following options can apply to YAML format input (I) and output (O):

  "grid_directory" (I) Base directory used for external grid source names
  "check_datasource_affine_coeffs" (I) Compare affine coeffs from data source with those defined in YAML (true or false)
  "use_nested_grids" (O) Create nested grids in the output YAML (true or false, default true)
  "use_griddata_section" (O) Use a gridData section for grid data (true or false, default true if more than one grid)

```

## gdal_to_ggxf_grid_headers.py

A basic script to read a GDAL grid data source and emit a YAML fragment containing the corresponding grid definitions that can be used install the grids into a GGXF YAML file.  If this is useful it could be enhanced to provide a more complete YAML template.  Note: GGXF.py has been amended to support inferring these parameters from a GDAL data source and not requiring them in the YAML header, and also checking the data source matches the YAML.  
