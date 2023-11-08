# Overview

This directory contains experimental python 3.8+ script to prototype working with GGXF datasets.

# Installation

The main program provided by these scripts is "ggxf", which may be used to convert between the YAML and NetCDF GGXF formats,
to give a very basic description of the contents of a GGXF file, and to calculate the parameters defined in the GGXF file at 
a set of points.

This script can be installed into a local environment using the python pip module.  Download the scripts module into a local
directory and then in that directory run 

```
python -m pip install .
```

This will install the scripts into the local Python environment.  Note that on Windows this may require adding the python 
local scripts directory to the PATH environment variable.  If this is required the installation will show a warning message 
advising that this is required.

Note that this installation does not include the python gdal module that is required for some of the functions of the ggxf script.
(See below for more information).

# Requirements

Running these scripts requires a Python 3.8+ environment with the following modules installed:

* numpy
* NetCDF4
* PyYAML
* GDAL (optional - provides extra capabilities and tools for importing data sets to GGXF)

Installing GDAL into the python environment can be difficult!  

In Windows a python environment manager such as [anaconda](https://anaconda.com) may be the simplest approach.  To install GDAL into an anaconda  enviroment use the conda command,

```shell
(myenv)$> pip install numpy netcdf4 pyyaml
(myenv)$> conda install -c conda-forge gdal
```
On Linux operating systems such as ubuntu the package management tool (eg apt) may provide the required python libraries.  

To install these modules into a virtual environment on linux may require first installing the NetCDF and GDAL development libraries into the operating system with the system package manager, and then installing the python modules into the development environment with pip.  This may require care to ensure that the version of the python module matches the installed development libraries:

For example:

```shell
$> gdalinfo --version
GDAL 3.4.1, released 2021/12/27
pip install GDAL==3.4.1
```

The ggxf script has an option to create .CDL files (a NetCDF ASCII dump format) which can be useful for understanding the contents of a NetCDF4 file (a GGXF binary file).
This requires installing the NetCDF4 ncdump utility, which can be obtained from the [NetCDF4 download page](https://downloads.unidata.ucar.edu/netcdf/).

# Scripts

This directory contains two scripts to support generating and experimenting with GGXF format files.

* ggxf.py - converts GGXF YAML <-> NetCDF, Calculate values from GGXF dataset, dumps GGXF summary data
* deformation_model_to_ggxf_yaml.py - compiles a GGXF YAML file from a JSON/GeoTIFF encoded deformation model

## ggxf.py script

This is the main utility built for processing GGXF files. It has four basic functions:

* ggxf.py convert - Converts files between YAML and NetCDF GGXF formats
* ggxf.py describe - Briefly describes the content of a GGXF file
* ggxf.py calculate - Evaluates the parameters of the GGXF file at CSV file of test locations.  (Note this does not apply the coordinate operation, just calculates the values it would use)
* ggxf.py import - Imports data from a [GDAL supported](https://gdal.org/drivers/raster/index.html)  grid file to a GGXF YAML.  This may include placeholders for missing attributes, or maybe supplied attributes from a YAML template.

Each of these options includes some online help available with the --help option (eg ggxf.py import --help).

### Convert a file between YAML and NetCDF formats

```shell
python3 ggxf.py convert -h
```

```text
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

Example:

```shell
python3 gxf.py convert -v PRGEOID18.yaml PRGEOID18.ggxf -n write-cdl=header
```

### Describe the contents of a GGXF file

```shell
python3 ggxf.py describe -h
```

```text
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

Example:

```shell
python3 ggxf.py describe -v ca_ntv2.ggxf --csv-grid-summary ca_ntv2_grids.csv > ca_ntv2_ggxf.txt
```

This will create a text file ca_ntv2_ggxf.txt containing a brief description of the contents of the file
and a CSV file ca_ntv2_grids.csv with one row for each grid in the data file.

### Calculate parameters values at a set of locations

```shell
python3 ggxf.py calculate -h
```

```text
usage: ggxf calculate [-h] [-n option=value] [-y option=value] [-d #]
                      [-e ####.#] [-b ####.#] [-g] [-v]
                      input_ggxf_file input_csv_filename output_csv_filename

Calculate parameters from a GGXF file

positional arguments:
  input_ggxf_file       Input GGXF file, either .yaml or .ggxf
  input_csv_filename    Input CSV file of point coordinates
  output_csv_filename   Results CSV file

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

Example:

```shell
python3 ggxf.py calculate nzgd2000-20180701.ggxf test_points.csv test_output.csv -e 2015.0 --csv-decimal-places=4
```

This takes in input file test_points.csv of points at which the deformation model in nzgd2000-20180701.ggxf is to be evaluated.
For example this file could contain

```csv
nodeLongitude,nodeLatitude
175.052,-41.05747
...
```

Because this is a deformation model it requires an epoch to evaluate the parameters, given by `-e 2015.0`.

The output file test_output.csv is:

```csv
nodeLongitude,nodeLatitude,displacementEast,displacementNorth,displacementUp
175.052,-41.05747,-0.2939,0.4986,-0.0013
```

### Import a GDAL compatible grid file into GGXF format

Note: The ggxf import function requires the Python gdal module to be installed in order to convert import GDAL grids.

```shell
python3 ggxf.py import -h
```

```text
usage: ggxf import [-h] [-m METADATA_FILE] [-c CONTENT_TYPE] [-a ATTRIBUTE]
                   [-p] [--ignore-errors] [-g] [-v]
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
  -e EPSG_CODES, --epsg-codes EPSG_CODES
                        Interpolation, source, and target EPSG codes separated by /                        
  -w, --write-template  Write metadata template to YAML file instead of GGXF
  -p, --include-placeholders
                        Include placeholder metadata in output GGXF YAML
  --ignore-errors       Less rigorous checking of GGXF YAML file
  -g, --debug           Generate debugging output
  -v, --verbose         More verbose output

Basic usage:
    ggxf import meta_template.yaml
        Creates a metadata template file meta_template.yaml

    ggxf import meta_file.yaml grid_file
        Includes metadata template.

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

Most GDAL grids do not contain all the metdata required by the GGXF format, so the import function provides some tools for adding this metadata.

Some GDAL grid formats are associated with specific content types.  For example NTv2 is associated with geographic2dOffsets, and ISG is associated with geoidHeight.  These can be defined in a YAML file such as [gdal_driver_parameters.yaml](https://github.com/opengeospatial/CRS-Gridded-Geodetic-data-eXchange-Format/blob/master/scripts/GGXF/gdal_driver_parameters.yaml) which will preset some of the metadata of the GGXF file.  

The import function can also use additional YAML metadata files to define attributes that the GGXF file requires.  For example, a producer
organisation may create a YAML file containing the organisation metadata that GGXF files require, or a file defining the licence with which data is published.

A good start to creating a metadata file is to use ggxf.py to create a template:

```shell
python3 ggxf.py import -w orgmeta.yaml
```

This will create a template file orgmeta.yaml which contains:

```yaml
content: Content type (mandatory) - eg geographic2dOffsets
title: Dataset title (mandatory)
abstract: Dataset abstract (mandatory)
comment: Comment on the dataset
contentApplicabilityExtent: Placeholder for applicability extent - put a description here if required
parameters: Placeholder for list of parameters
interpolationCrsWkt: EPSG:0000
sourceCrsWkt: EPSG:0000
targetCrsWkt: EPSG:0000
licenseURL: URL of license
operationAccuracy: Representative accuracy of coordinate operation (replace with a number)
publicationDate: Publication date of dataset
version: Version of the dataset
digitalObjectIdentifier: Digital object identifier of the dataset
partyName: Organisation name of the producer/publisher
electronicMailAddress: Email address of the producer/publisher
onlineResourceLinkage: URL of producer/publisher website (or specific page about the dataset)
deliveryPoint: Street address of the producer/publisher
city: City of the producers/publisher's address
postalCode: Postal code of the producer/publisher's address
country: Country of the producer/publisher's address
interpolationMethod: bilinear
```

Each line in this can be updated with the required value, or deleted from the file.  For example, an organisation metadata file
might just include `partyName`, `electronicMailAddress`, and `onlineResourceLinkage`.

A source file can then be converted to GGXF (either YAML or NetCDF) with a command such as:

```shell
python3 ggxf.py nzvd2016.ggxf NZGEOID2016_20161102.isg -m linz.yaml -m licence.yaml -a interpolationCrsWkt=epsg:4167 -a sourceCrsWkt=epsg:4959 -a targetCrsWkt=epsg:7839
```

Alternatively the -p option can be used to create a YAML GGXF file containing placeholders for the metadata attributes, for example:

```shell
python3 ggxf.py import -p nzvd2016-template.yaml NZGEOID2016_20161102.isg -e 4167/4959/7839
```

(Note: this example is using the shorter -e option for specifying EPSG codes)

The nzvd2016-template.yaml file can then be edited to insert the correct metadata.  Note that some metadata must be replaced (eg operationAccuracy metadata attribute must be deleted or replaced with a numeric value).  

It is recommended that the EPSG codes for the interpolation, source,
and target crs are specified so that they can be replaced with the full WKT specification required by GGXF.

Note that the import function creates a GGXF YAML which references the source grid file for the grid data.  The ggxf script will read the grid parameters from the source grid file.  An example of the grid definition in the template file is:

```yaml
  - gridName: NZGEOID2016_20161102.isg
    affineCoeffs: [-24.983333333333334, 0.0, -0.016666666666666666, 159.98333333333332,
      0.016666666666666666, 0.0]
    iNodeCount: 1801
    jNodeCount: 2101
    dataSource:
      dataSourceType: GDAL
      gdalSource: NZGEOID2016_20161102.isg
```

The `ggxf convert` option can be used to load the grid data from the external GDAL format into into either a NetCDF file or a "native" GGXF YAML file.

```shell
python3 ggxf.py convert nzvd2016-template-edited.yaml nzvd2016.yaml 
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
