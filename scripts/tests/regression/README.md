# Regression tests

Simple regression tests to check the basic operation of the ggxf utility.  Each test file contains
a list of files to use for the test (sourced from ../data) and the ggxf command arguments to run
the test.  The test is run in a directory out/<testname> and the resultant files are compared with
the check directory check/<testname>.

Note: This is currently an incomplete list of tests.  In particular it is does not include the deformation
model examples which include multiple grids, and more than one parameter in each grid.

## Basic tests with a single parameter (geoid file)

 Test | Description
 ---  | ---
01-yaml-inline-io | Tests reading/writing inline YAML grid data
02-yaml-inline-to-csv | Tests writing to YAML with CSV grid file
03-yaml-inline-to-netcdf | Tests writing to NetCDF GGXF file
04-yaml-with-csv | Tests reading YAML with CSV grid file
05-yaml-gdal-load | Tests reading YAML with GDAL external source
06-netcdf-io | Tests reading a NetCDF GGXF file
07-calc-geoid | Tests linear interpolation of the geoid model
