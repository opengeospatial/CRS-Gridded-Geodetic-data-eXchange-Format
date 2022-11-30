# Example GGXF data sets

The subdirectories of this folder contain example GGXF data sets for a number of content types.  
Each directory contains one or more YAML representations of a GGXF data set.
Included in each directory is one or more YAML definitions.  

Note: Most of these use the CSV and GDAL data source option which is an implementation customisation
of the ggxf.py script in this repository to load grid data from external data files.  The GGXF
specification allows the dataSource attribute of a GGXF grid to specify an external data source from
a YAML grid definition, but the use of this attribute is an implementation specific customisation.

The contents of the dataSource attribute in the YAML examples is not a GGXF specification.

The directories also include:

* NetCDF formatted binary GGXF data sets (*.ggxf),
* NetCDF CDL text representation of the structure of the NetCDF data set (*.cdl)
* Example calculations of the spatial function defined by the spatial GGXF data sets. Includes test_points.csv (input coordinates), test_points-out.csv (output coordinates), test_points-out.csv.chk (expected results in test_points-out.csv for checking)
* Shell scripts to convert YAML files to GGXF files (compile_ggxf.sh)
* Shell scripts to calculate the function defined by the GGXF dataset (calc_ggxf.sh)

The example directories include:

| Directory | Contents
| --- | ---
| GGXF-specification-examples | Example grids from the deformation model specification document.  Note these examples do not contain grid data.  The ggxf.py script is used to validate these examples and generated NetCDF cdl headers from them by populating grids with dummy data.
| deformationModel/LINZ-NewZealand-NZGD2000 | The New Zealand NZGD2000 deformation model
| deviationsOfTheVertical/NGS-PRVI-DOV18 | An example deviation of vertical data set based on a Puerto Rico data set to show a GGXF dataset not used for coordinate transformations
| geoidModel/NGS-PRVI-Geoid18 | Full examples of a geoid datasets for Puerto Rico and the Virgin Islands.  This demonstrates alternative representation of the grid data in the GGXF file.
| geographic2dOffsets/NRCAN-Canada-NTv2 | Full example of the Canadian NTv2 transformation grid demonstrating a nested grid data set.
| velocityModel/NGS-Alaska-HTDP | An example of a non-nested grid data set based on the Alaskan velocity grids of the US HTDP deformation model.  Warning: this does not exactly represent the Alaskan velocity model as in HTDP the St. Elias grid has a non-rectangular domain of validity.  To implement this in GGXF will required splitting the grid into two grids with different grid priorites relative to the South Central grid.
