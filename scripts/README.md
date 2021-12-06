# ggxf_yaml_to_netcdf4.py

This is an experimental python 3.8+ script to test NetCDF4 encoding options for a GGXF.

## Usage

```
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

This implementation also includes a very limited test of using NetCDF4 compound data types to represent attributes.  Currently only 
parameter definitions supported.

## Installation

This script requires installing python3 modules netCDF4, pyyaml, and numpy.  If grids are defined using a dataSource attribute then the gdal module is also required.  

## Issues

* Integer attributes (such as list counts) are encoded with data type long long, for example "3LL".  This doesn't affect usage, but could impact on decoding with other tools.  This may be a constraint of the netCDF python library - to be investigated.

* Implementation using NetCDF4 compound types is very limited.  If this option is preferred for some or all attributes this will need to be addressed.

* Currently grid data are encoded as a (nrow,ncol,nparam) dimensioned variable.  One other option that has been proposed is using a separate (nrow,ncol) variable for each parameter - this is not provided as an option here.  Another option that could be implemented for grids with just one parameter is to collapse (nrow,ncol,1) dimension arrays to (nrow,ncol) arrays.

* A partial JSON option implementation might be useful where are genuinely metadata (ie data about the data) are encoded into a JSON formatted metadata attribute rather than encoding as CDF attributes, particularly if this matches a JSON format used for discovery/search.

* Implementation - this is currently implemented as a single python script.  Once the NetCDF implementation is decided it will be better implemented with as a GGXF module with options for reading and writing both YAML and NetCDF representation, as well as schema validation.  
