# Overview

This directory contains experimental python 3.8+ script to test NetCDF4 encoding options for a GGXF.
These scripts are intended for experimenting with the GGXF format - they are not "production ready".  

## GGXF module

The GGXF directory contains an under development.  It is intended as a prototype python module for handling GGXF files.  There is also a placeholder script GGXF.py in the source directory which just runs the App.py script in the GGGXF directory.

* Reading and writing a NetCDF4 GGXF file
* Reading and writing a YAML format GGXF file
* Calculating the GGXF grid value at a set of points in a CSV formatted file (with columns X and Y corresponding to the first and second ordinates of the interpolation coordinate system).  If there is more than one group in the GGXF file it calculates values for every group.  This currently does not handle deformation models or time functions and only implements bilinear interpolation.
* Dumping a single grid from the GGXF file as a CSV file of coordinates and values with one row for each grid node (mainly for checking the grid layout/affine transformation is correct)
* Adding deformation model time functions and calculating the deformation model
* Implementing biquadratic and bicubic interpolation functions
* Checking the GGXF content attribute to ensure the content type is correct and group parameters match the content type.

Intended development includes:

* Handling of summation of uncertainty for deformation.  RMS?
* Support for "no-data" value
* ? Handling of covariance for deformation
* ? Support for non-GGXF data in grid
* ? Lazy loading of grid data
* Test suite

If it is to be adapted for production use it will also require

* A lot of documentation
* Packaging

The scripts/GGXF.py runs a basic command line application for testing.  The options provided by this will change as the program is developed.  To see the command line usage run the command

``` sh
python3 GGXF.py -h
```

Options listed at the time of writing are:

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
