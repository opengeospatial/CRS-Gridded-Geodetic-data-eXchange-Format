# GGXF : Gridded Geodetic data eXchange Format

This repository holds the artefacts of the GGXF project team.  This work has culminated in the adoption of the standard [OGC GGXF geodetic data grid exchange format](https://docs.ogc.org/is/22-051r7/22-051r7.pdf) which is maintained on the [OGC Standards](https://www.ogc.org/standards/) page.

The purpose of the Gridded Geodetic Data Exchange Format (GGXF) project team is to design a file structure and computer storage mechanism for the efficient exchange of regularly gridded geodetic data. There are several open issues that need to be refined in an open collaborative environment. This will be achieved by:

- Defining what is meant by “gridded geodetic data”
- Establishing the use case(s) for the GGXF
- Defining the user needs for a GGXF
- Defining the requirements of a GGXF
- Evaluating existing grid formats used for the exchange of geodetic data
- Determining the deficiencies of existing grid formats
- Designing the grid structure
- Designing the header structure
- Designing the GGXF file structure
- Develop a strategy for encoding the file
- Develop a strategy for promulgating the format as a standard for the geodetic community

The work will be conducted under the auspices of the OGC CRS DWG.  The GGXF format is intended to support geodetic gridded data used in coordinate transformations including deformation models.  This team is working in close collaboration with the CRS DWG project team developing the “Deformation Functional Model” (DFM) that is specifying these requirements. On completion of the work, a Standards Working Group shall be chartered and materials passed over to the SWG for finalising into a Standard.

# Contents

The [current draft of the GGXF specification](https://github.com/opengeospatial/CRS-Gridded-Geodetic-data-eXchange-Format/raw/master/specification/GGXF%20v1-0%20OGC-22-051r7_2024-01-08.pdf)
is available for download as a PDF from the specification directory in this repository.

The [examples](https://github.com/opengeospatial/CRS-Gridded-Geodetic-data-eXchange-Format/tree/master/examples) directory contains examples of GGXF data sets in both YAML (text) and NetCDF (binary) formats.

The [scripts](https://github.com/opengeospatial/CRS-Gridded-Geodetic-data-eXchange-Format/tree/master/scripts) directory contains example python scripts used to compile the example GGXF data sets and test implementation options during the development of the specification.

# Collaboration

This is a public repository - everything is visible to anyone coming to this website. If you wish to be an active contributor with write access then you will need [join github](https://github.com/) if you haven't already. Once you are signed on to github please raise a [new issue](https://github.com/opengeospatial/GGXF/issues/new) with a request to be added. If you would like to be included on the Project Team page then include a brief biography and a photo. This is not required - be aware that everything on the page is visible to the public - but it is good to have faces for names!

Also once you have a github id you are encouraged to click the "Watch" button at the top of this page so that you will be notified of postings in the issues log. Ideally we can capture most of the discussion in the issue logs where they will be recorded and easily searchable. We will create an issue for each major discussion topic.

# Existing Work

This work is based on the Esri GGXF model built on [NetCDF](https://www.unidata.ucar.edu/software/netcdf/); more information can be found at [Esri GGXF](https://github.com/Esri/ggxf).
