# Overview

This directory contains experimental python 3.8+ script to test NetCDF4 encoding options for a GGXF.
These scripts are intended for experimenting with the GGXF format - they are not "production ready".  

### Scripts

This directory contains three scripts to support generating and experimenting with GGXF format files.

* ggxf.py - converts GGXF YAML <-> NetCDF, Calculate values from GGXF dataset, dumps GGXF summary data
* deformation_model_to_ggxf_yaml.py - compiles a GGXF YAML file from a JSON/GeoTIFF encoded deformation model

### ggxf.py script

This is the main utility built for processing GGXF files. It has four basic functions:

* ggxf.py convert - Converts files between YAML and NetCDF GGXF formats
* ggxf.py describe - Briefly describes the content of a GGXF file
* ggxf.py calculate - Evaluates the parameters of the GGXF file at CSV file of test locations.  (Note this does not apply the coordinate operation, just calculates the values it would use)
* ggxf.py import - Imports data from a GDAL supported grid file to a GGXF YAML.  This may include placeholders for missing attributes, or maybe supplied attributes from a YAML template.

Each of these options includes some online help available with the --help option (eg ggxf.py import --help).

## GGXF module

The GGXF module contains scripts for reading and writing GGXF files in YAML and NetCDF format, and for calculating values from the GGXF grids.  It also supports extracting some summary information from GGXF files, in particular a summary of the grids in the file.  

This code has evolved alongside the specification and contains several options for alternative GGXF format choices that have been experimented.  Its main purpose has been to build example GGXF files and demonstrate the feasibility and impact of implementation choices.

There is a placeholder script ggxf.py in the source directory which just runs the App.py script in the GGGXF directory.  This provides functions for:

* Reading and writing a NetCDF4 GGXF file
* Reading and writing a YAML format GGXF file
* Calculating the GGXF grid value at a set of points in a CSV formatted file (with columns X and Y corresponding to the first and second ordinates of the interpolation coordinate system).  If there is more than one group in the GGXF file it calculates values for every group.  This currently does not handle deformation models or time functions and only implements bilinear interpolation.
* Dumping a single grid from the GGXF file as a CSV file of coordinates and values with one row for each grid node (mainly for checking the grid layout/affine transformation is correct)
* Adding deformation model time functions and calculating the deformation model
* Implementing biquadratic and bicubic interpolation functions
* Some parameter and content type validation.

### deformation_model_to_ggxf_yaml.py

An experimental script to convert a JSON/GeoTIFF format deformation file to GGXF YAML.  Under development.
