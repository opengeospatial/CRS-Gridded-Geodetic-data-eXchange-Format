Example NTV2 grid - Natural Resources of Canada NTv2 grid
====================================================================

This is the Canadian NTv2 version from <https://webapp.geod.nrcan.gc.ca/geod/data-donnees/transformations.php>

This is loaded using the dataSource YAML attribute from the NTV2_0.GSB file.  The YAML for the GGXF group was created using the script build_group_yaml.sh,
which in turn uses the python script gdal_to_ggxf_grid_headers.py.  This includes a configuration to reverse the sign of the longitudeOffset to match then
expected direction of east positive.

The file test_points.csv contains a few points to test the grid, including two different parent grids and a point on the Banff subgrid.
