# Selection of GGXF carrier file format

The GGXF specification is defined with a carrier-neutral core expressed in a text format (YAML).
Multiple text or binary formats can be used as “implementations” of GGXF.
In this first version of the specification, only one binary carrier is defined,
based on netCDF-4 which is itself a profile of HDF5.
That format has been preferred to alternatives (text, NTv2, GeoTIFF and ZARR) for reasons stated in this page.
However this choice does not exclude the use of other carriers as alternative “implementations” in future versions.

Below is the list of desired features for a carrier,
followed by discussions about how the candidate formats met those goals.

* Standardized by an international organization such as OGC.
* Supported by mainstream software and programming languages.
* Can be decoded efficiently by software.
* Can store 2, 3 or 4-dimensional arrays.
* Can organize data as trees of nested grids of different domains and resolutions.
* Can serialize data in tiles or chunks for efficient reading of a sub-domain.
* Allow downloading of only the required parts of files from a storage service on the cloud.
* Capable to store rich metadata (three Coordinate Reference Systems, uncertainties, etc.).
* Fully self-descriptive, without the need to be completed by an external database.
* Distributed as a single file (for reducing the risk on geospatial data integrity).

The last goal in above list is based on the observation that integrity of geospatial data
distributed as a set of files (for example Shapefiles or World Files)
is easily compromised by forgetting to join auxiliary files together with the main file,
or by filling a missing file with a copy of an auxiliary file designed for another dataset.
Packaging the data as a ZIP file reduces the risk,
but the problem still exists especially if data must be unzipped before they can be used.
Data packaged in a single binary file are more difficult to corrupt
since modifications require the use of specialized software.



## Text formats

Text formats such as XML, JSON or YAML are readable by humans,
which is important at least for header information.
Those formats are useful for data producers and for end users wanting to inspect the data.
However text formats are not efficient for consumption by map projection libraries.
Parsing a text file is more costly for software than reading a binary file,
and it is difficult to read arbitrary subsets of a text file.
Binary files are more suitable to grids of any size, including large ones,
and are easier to subdivide in tiles or chunks of constant size.

The group decided that GGXF data should be distributed and used in a binary format,
but we need a utility to dump header records and small grid extracts in a text format.
Adopting YAML gives a structure of the text format which may be used in file creation,
and for end user human-readable summary.



## Binary version of YAML file

We briefly considered to define our own binary format derived from the YAML text format,
but it would require new software to both produce and consume.
It would require a large effort for defining all required details
(how to encode attributes, dimensions, groups, chunks, etc.),
which would duplicate existing generic binary carriers such as ZARR or HDF5 for no benefit.



## NTv2 format

The NTv2 format is a de facto standard (except in United States) for geographical two-dimensional offsets.
It has several proprietary extensions, for example for two-dimensional velocity grids.
But NTv2 is not readily extensible to other geodetic content types or higher number of dimensions.
NTv2 supports nested grids, but not overlapping grids.
It does not support tiling, which makes it inefficient for large grids.



## ZARR format

ZARR encodes data as a set of files, which goes against the “single file” goal.
The splitting in many files is presented as an advantage for storage on cloud,
but the Cloud Optimized GeoTIFF (COG) convention is an example of alternative approach
achieving similar performance benefits with a single file.

Both GeoTIFF and netCDF are standardized by the Open Geospatial Consortium (OGC)
and are supported by mainstream programming languages.
But the ZARR format is not yet an OGC standard (at the time of writing this page)
and its development is still quite active.
Furthermore as a format originally designed for the Python community,
it has less support (for now) than GeoTIFF and netCDF in other programming languages.
For those reasons, using the ZARR format in version 1.0 of GGXF would be premature.



## GeoTIFF format

GeoTIFF is the most popular format among the candidates.
As an extension of TIFF format,
it can be visualized (even if not geolocalized) by ubiquitous software such as web browsers.
GeoTIFF readers and writers exist in mainstream programming languages.
Images can be tiled, and the “Cloud Optimized GeoTIFF” (COG) convention adds a pyramid on top of tiled images
for allowing efficient data extractions of various sub-regions at various sub-sampling from a single file stored on the cloud.
The Coordinate Reference System (CRS) and its mapping from pixel coordinates are defined with sufficient details
for allowing accurate positioning when the CRS is geographic or projected with (east, north) axis order.
GeoTIFF is familiar to many geospatial software implementers
and has been adopted by the PROJ open source community as a pivot format for datum shifts.

However GeoTIFF is a rigid format compared to netCDF.
It can only store metadata elements that are defined either by the TIFF specification, or by the GeoTIFF specification.
Any metadata element defined outside TIFF or GeoTIFF have to be stored in another format, typically XML or JSON.
It results in an heterogeneous set of formats either nested inside the TIFF file or added as auxiliary files:

* ISO 19115 metadata as an XML document stored as a character string in TIFF tag `C6DD`.
* GDAL-specific metadata as an XML document stored as a character string in TIFF tag `A480`.
* PROJ-specific metadata about datum shifts stored as an auxiliary JSON file.
* GeoTIFF keys (GeoKeys) are themselves a custom format stored in a few TIFF tags.
  * The values of some GeoKeys are themselves a third layer of format.
    For example there is a key for the name of geographic CRS (`GeogCitation`) but no keys for its components.
    Consequently some GeoTIFF files encode the names of all components in a single character string like below:
    ```
    GCS Name = wgs84|Datum = unknown|Ellipsoid = WGS_1984|Primem = Greenwich|
    ```

The rigidity in GeoTIFF metadata causes restrictions described in following sections.
Those restrictions can not be resolved with existing TIFF tags and GeoTIFF keys,
and new tags or keys can not be easily added.
New tags must be registered by sending a request to Adobe (owner of the TIFF specification).
Finally we note that GeoTIFF is not used by any geodetic data producers to our knowledge,
except for exporting their grids to PROJ.



### GeoTIFF restrictions on Coordinate Reference Systems

GGXF file needs to declare three Coordinate Reference Systems (CRS):
the source, the target and the interpolation CRS.
But a GeoTIFF file can declare only one CRS, the interpolation one (i.e. the CRS for pixel locations).
The two other CRS have to be either inferred from the context
(the source and target CRS of the Coordinate Operation containing the file as a parameter value in the EPSG database),
or be supplied in an auxiliary file.
The former goes against the “self-descriptive” goal and the latter goes against the “single file” goal.

Furthermore CRS in GeoTIFF files are restricted to geodetic or projected CRS with (east, north) axis order,
optionally completed by a vertical CRS.
By contrast another GGXF goal is to be usable for a wider range of CRS,
including CRS with more than two dimensions, CRS of engineering, parametric or temporal types,
and CRS in polar regions where axis directions are like “South along 90°E meridian”.



### GeoTIFF restriction on nested grids

GGXF must be at least as capable as NTv2.
An NTv2 file can contain a grid for the whole country and many grids at finer resolutions for some specific sub-regions.
The grids can form a tree where each parent grid contains an arbitrary amount of nested grids (children).
GGXF goes further by allowing also overlapping grids or grids without parent-child relationship.
Those use cases are not handled by the Cloud Optimized GeoTIFF (COG) convention,
because COG establishes a relationship between grids at different resolutions
but with the restriction that they all share the same domain.
The NTv2 use case could be handled by defining new conventions,
but there is no natural solution under TIFF framework.
The tree structure would need to be defined in an auxiliary file, or in new GeoTIFF keys,
or inferred by a (possibly error-prone) comparison of GeoKeys in each grid.

The PROJ Geodetic TIFF grids (GTG) format uses a GDAL-specific TIFF tag (`GDAL_METADATA`)
for encoding in a XML document the metadata not supported by GeoTIFF,
which includes a `parent_grid_name` item.
But PROJ itself ignores that item and rather infers grid relationships from their extents.
That convention supports a single root grid, and requires strict nesting
(child grids fully contained and not overlapping)
to allow unambiguous resolution by extents.



### GeoTIFF restrictions on data cubes

The TIFF format is designed for two-dimensional images.
A convention for storing multi-dimensional (N-D) arrays has been proposed in OGC TestBed 17,
but it requires the use of new GDAL-specific metadata; there is no natural solution within TIFF.
Furthermore the COG and N-D conventions both use the same TIFF capability to store many images in the same file,
so the interactions between those two conventions when they coexist can be complex.

GeoTIFF can stores integers, floating point values, fractions and complex numbers.
It can not store data structures other than the predefined ones.
A data structure not yet used but of potential interest in future GGXF versions is matrix.



### GDAL metadata

The PROJ Geodetic TIFF grids (GTG) format workarounds TIFF limitations
by storing an XML document in the `GDAL_METADATA` TIFF tag.
Elements defined by GTG specifications are
`SCALE`, `OFFSET`, `TYPE`, `DESCRIPTION`, `UNITTYPE`,
`target_crs_epsg_code`, `target_crs_wkt`,
`source_crs_epsg_code`, `source_crs_wkt`,
`interpolation_crs_wkt`, `recommended_interpolation_method`, `area_of_use`,
`grid_name`, `parent_grid_name` and `number_of_nested_grids`.
But that tag is specific to the GDAL project, and (at the time of writting this page)
has not been registered by Adobe as a reserved TIFF tag.
This tag is (at least informally) owned by the GDAL community,
which implies that its content can not be defined by OGC except through collaboration with GDAL.

In addition of `GDAL_METADATA`, PROJ also uses metadata stored in an auxiliary JSON file.
The use of `GDAL_METADATA` and auxiliary JSON file are two ways to achieve the same goal:
workaround TIFF limitations by attaching documents in other formats.
Those two auxiliary documents are needed together for deformation models.



## NetCDF-4 format

The netCDF-4 format can be seen as a binary XML where values are multi-dimensional arrays instead of texts.
Like XML or JSON, the netCDF format puts no restriction on the metadata (attributes) that it can contain and on the meaning of data.
Arrays can be not only gridded data, but also geometries, features, time series, point cloud and more.
This flexibility come with an interoperability cost:
a given netCDF file can easily contain metadata that most software do not know how to interpret.
But this is not different than XML or JSON:
for enabling data exploitation, these formats must be completed by a schema.

The CF-Conventions can been seen as a schema defined by the Climate and Forecast community for netCDF files.
It is the most widely used schema, but not the only one.
For example the Attribute Convention for Dataset Discovery (ACDD)
is another set of conventions which complement the CF-Conventions.
Highly specialized datasets using their own conventions are not rare
(and contribute to the apparent lack of interoperability of netCDF format),
but they often reuse some elements from ACDD and CF-Conventions when applicable.
GGXF itself falls in this category, for reasons developed below.



### CF-Convention limitations on Coordinate Reference Systems

The ACDD and CF-Conventions define a rich set of metadata including geographic and temporal extents,
producer information, lineage, units of measurement, pad values and more.
However CRS definitions in these conventions were used to be quite approximate (the situation is improving).
But this is a weakness of conventions used as schema,
not a weakness of netCDF format itself which allows the use of arbitrary conventions.
Because of netCDF flexibility,
the CF-Convention parts related to referencing by coordinates can cleanly be replaced by a GGXF convention.
This replacement is justified by the fact that referencing is the whole purpose of GGXF,
and that the netCDF format treats all conventions as equally good.

GGXF encodes CRS definitions as character strings in Well Known Text (WKT) format,
which is a “format nested into format” oddity similar to the ones raised against GeoTIFF.
However its existence is not imposed by format constraints, but a choice for reducing complexity.
Since GGXF is aimed for consumption by map projection libraries,
the availability of an ISO-19162 compliant WKT parser seems a reasonable assumption.
Invoking the existing parser for a single character string is easier
than fetching many attributes for all CRS components and assembling them.

Above departure from CF-Conventions implies that existing software
will not be able to georeference GGXF data without software updates.
But this interoperability problem is to be nuanced,
because existing software would not know how to use grid data in the context of coordinate operations anyway.
Dedicated code is required for handling GGXF particularities (e.g. the three CRS)
and for using data differently than classical raster processing:
inside a chain of coordinate operations,
as opposed to visualization or calculations using cell values after all coordinate operations.
It sometime means that the code needs to live in a completely different module or project,
for example PROJ instead of GDAL.
Note that this need for specialized code would be the same with GeoTIFF format.



### Efficient loading of grid subsets

Cloud Optimized GeoTIFF (COG) allows the use of gridded data in various sub-regions and resolutions
without forcing applications to download the whole grid from the web.
COG is not really a format, but rather a set of good practices and conventions.
These good practices are mostly format-neutral and their application to netCDF is discussed below.

GGXF grids may be large, and applications may need to load grids for only some sub-regions.
A typical way to make that process efficient is to divide grids into smaller tiles or chunks of equal sizes.
This feature is supported natively by both TIFF and netCDF-4 (but not by netCDF-3).
NetCDF-4 has the additional advantage of supporting chunks in any number of dimensions,
while TIFF tiles are only two-dimensional.

In addition to sub-regions, applications may also need to use grids at different resolutions.
COG provides a convention for identifying which images in a TIFF file should be interpreted as levels in an image pyramid.
Such convention is less needed with netCDF-4 because that format supports trees of nested grids natively.
Some conventions are still needed,
but netCDF-4 provides a more advanced framework than TIFF as a basis for structuring patchworks of grids.

Applications should be able to download only the required parts of a file for given sub-region and resolution.
COG facilitates that optimization by concentrating all metadata at the beginning of the file
(as opposed to having metadata scattered through the file).
This recommendation is valid for any format where metadata positions are flexible,
and can be applied to netCDF as well.



### NetCDF support in software

The GeoTIFF format has more widespread support,
with both readers and writers in many programming languages.
NetCDF-4 has readers in mainstream languages too (C/C++, Java, JavaScript, Python),
but no know writers other than the C/C++ one provided by the HDF group.
This is not necessarily an indication of format complexity however;
the community size and history are also important factors.
GeoTIFF is based on TIFF, which was extensively used by large industries such as scanner manufacturers.
TIFF also exists for a longer time than netCDF-4,
which gave time to resolve TIFF own complexity problems
(before version 6, a joke was that TIFF stands for “Thousands of Incompatible File Formats”).

Commonly used TIFF libraries in C/C++ language tend to be more lightweight than their HDF5 counterpart.
The `libhdf5` C/C++ library is more than 7 times larger than `libtiff`
(4.1 Mb compared to 547 kb on Linux distribution as of 2022).
Furthermore the use of `libhdf5` in multithreaded environments is reported as problematic.
Those drawbacks are not necessarily important for data producers,
because GGXF files are not written as often as they are read,
and data may be produced by applications fully dedicated to this task.
But those drawbacks are much more problematic for data users,
where reading GGXF files is only one task among many others,
and where there is a desire to avoid to double the size of PROJ (for example) because of HDF5.
However a lightweight read-only and thread-safe library for a subset of HDF5 features is technically possible.
The “Pyfive” project (a pure Python HDF5 file reader) is about 1700 lines of code.

Finally we note that some geodetic data producers have familiarity with netCDF.



## Conclusion

No format fits perfectly all requirements.
GeoTIFF and HDF5 (basis of netCDF-4) are two stable and standardized formats.
GeoTIFF is popular in geospatial software in general,
but netCDF is more familiar to geodetic data producers.
GeoTIFF has the most extensive software support,
but has little flexibility and poor metadata support compared to netCDF.
GeoTIFF is efficient for two-dimensional images associated to a single geographic or projected CRS constrained to (east, north) axes,
but can hardly goes beyond that scenario without the help of auxiliary files.
A single CRS is not sufficient for a fully self-descriptive GGXF file, trees of nested grids are needed,
and the need for three-dimensional grids is a reasonable expectation for the foreseeable future.

NetCDF-4 can do everything that Cloud Optimized GeoTIFF can do,
often in a cleaner way (without the patchwork of layers that are GeoKeys and embedded XML documents).
It can also do much more, with rich metadata, nested grids and true multi-dimensional support among other features.
Its flexibility implies more diversity in published data,
which makes impossible to guarantee that a single reader will understand the content of every netCDF files.
But this apparent netCDF interoperability problem is to be nuanced because data consumed by specialized software
– including GGXF – often require dedicated code anyway, even with GeoTIFF.
The main netCDF drawback is the characteristics of `libhdf5` in C/C++ programming language.
But lightweight readers exist in languages other than C/C++ for a subset of HDF5 features.
The work needed for doing something equivalent in C/C++ does not seem unreasonable.
By contrast, GeoTIFF shortcomings can not be fixed;
we would have to add yet more layers in external formats (XML, JSON…)
sometime overriding GeoTIFF metadata (e.g. CRS not supported by GeoTIFF).

GGXF aims to support not only the existing gridded geodetic data,
but also to pose the foundation for future developments.
A part of OGC TestBed 18 is already exploring potential use of existing standards
(including ISO 19111) in the context of Einstein’s relativity.
While out-of-scope of current GGXF specification,
general relativity is a legitimate need which may fit nicely in a GGXF extension supporting 4-dimensional grids
and (possibly) matrix or tensor values.
This is not necessarily a distant concern;
accurate GPS positioning for example depends on correct handling of general relativity.



### Summary

The following table summarizes the pros and cons of formats.
The absence of a check mark in a cell does not mean that the corresponding functionality is impossible to do.
It only means that it is not “natural” in that format.
Most functionality can be added to any format with extensions,
auxiliary files or command-line tools (`gzip`, `ncdump`…).
But doing so requires more work for the specification and for implementers.

|                                              | Text | NTv2 | ZARR | GeoTIFF | NetCDF |
| :------------------------------------------- | :--: | :--: | :--: | :-----: | :----: |
|Standardized by an international organization |      |      |      | X       | X      |
|Human-readable                                | X    |      |      |         |        |
|Supported by mainstream software              |      |      |      | X       | X      |
|Can be decoded efficiently by software        |      | X    | X    | X       | X      |
|Can store 3 or 4-dimensional arrays           |      |      | X    |         | X      |
|Can organize data as trees of nested grids    |      | X    | X    |         | X      |
|Can serialize data in tiles or chunks         |      |      | X    | X       | X      |
|Allow downloading of only the required parts  |      |      | X    | X       | X      |
|Capable to store rich metadata                | X    |      | X    |         | X      |
|Fully self-descriptive                        | X    |      | X    |         | X      |
|Distributed as a single file                  |      | X    |      |         | X      |
