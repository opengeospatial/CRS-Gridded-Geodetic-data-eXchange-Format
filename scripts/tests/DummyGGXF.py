from GGXF import GGXF

params = [
    {
        GGXF.PARAM_ATTR_PARAMETER_NAME: GGXF.GGXF_PARAMETER_DISPLACEMENT_EAST,
        GGXF.PARAM_ATTR_UNIT_SI_RATIO: 1.0,
        GGXF.PARAM_ATTR_UNIT_NAME: "meter",
    },
    {
        GGXF.PARAM_ATTR_PARAMETER_NAME: GGXF.GGXF_PARAMETER_DISPLACEMENT_NORTH,
        GGXF.PARAM_ATTR_UNIT_SI_RATIO: 1.0,
        GGXF.PARAM_ATTR_UNIT_NAME: "meter",
    },
    {
        GGXF.PARAM_ATTR_PARAMETER_NAME: GGXF.GGXF_PARAMETER_DISPLACEMENT_UP,
        GGXF.PARAM_ATTR_UNIT_SI_RATIO: 1.0,
        GGXF.PARAM_ATTR_UNIT_NAME: "meter",
    },
]

crswkt = """GEOGCRS["NZGD2000",
DATUM["New Zealand Geodetic Datum 2000",
ELLIPSOID["GRS 1980",6378137,298.2572221,LENGTHUNIT["metre",1,ID["EPSG",9001]],
ID["EPSG",7019]],ID["EPSG",6167]],CS[ellipsoidal,3,ID["EPSG",6423]],
AXIS["Geodetic latitude (Lat)",north,ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]]],AXIS["Geodetic longitude (Lon)",east,ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]]],
AXIS["Ellipsoidal height (h)",up,LENGTHUNIT["metre",1,ID["EPSG",9001]]],ID["EPSG",4959]]"""


def dummyGGXF():
    metadata = {
        GGXF.GGXF_ATTR_CONTENT: GGXF.GGXF_CONTENT_DEFORMATION_MODEL,
        GGXF.GGXF_ATTR_INTERPOLATION_CRS_WKT: crswkt,
    }
    return GGXF.GGXF(metadata, source="DummyGGXF")


def dummyGroup(
    nparam: int = 1, method=GGXF.INTERPOLATION_METHOD_BILINEAR, timefunc=None
):
    if nparam == 1:
        gparams = params[2:]
    elif nparam == 2:
        gparams = params[:2]
    else:
        gparams = params

    metadata = {
        GGXF.GROUP_ATTR_INTERPOLATION_METHOD: GGXF.INTERPOLATION_METHOD_BILINEAR,
        GGXF.GROUP_ATTR_TIME_FUNCTIONS: timefunc,
        GGXF.GROUP_ATTR_GRID_PARAMETERS: gparams,
    }
    return GGXF.Group(dummyGGXF(), "DummyGroup", metadata)
