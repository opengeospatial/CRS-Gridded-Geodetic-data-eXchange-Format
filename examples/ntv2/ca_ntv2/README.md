Example NTV2 grid - Natural Resources of Canada NTv2 grid
====================================================================

This is the Canadian NTv2 version from <https://webapp.geod.nrcan.gc.ca/geod/data-donnees/transformations.php>

This is loaded using the dataSource YAML attribute from the NTV2_0.GSB file.  The script gdal_to_ggxf_grid_headers.py was used to compile the list of grids.

The file test_points.csv contains a few points to test the grid, including two different parent grids and a point on the Banff subgrid.

<b>NOTE</b>  The output generated in testpoints.out differs from the correct value in that the longitudeOffset it calculates is for a west positive longitude, which is how the NTv2 file is constructed.  
This could be handled in GGXF by either adding some capability to transform the offset when the grid is loaded into the GGXF file (as a dataSource parameter?), or by defining the parameter as a west positive longitude shift in the GGXF group.
