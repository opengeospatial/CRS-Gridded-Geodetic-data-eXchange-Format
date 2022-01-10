from GGXF import GGXF

params = [
    {
        GGXF.PARAM_ATTR_PARAMETER_NAME: GGXF.GGXF_PARAMETER_DISPLACEMENT_EAST,
        GGXF.PARAM_ATTR_UNIT_SI_RATIO: 1.0,
        GGXF.PARAM_ATTR_LENGTH_UNIT: "meter",
    },
    {
        GGXF.PARAM_ATTR_PARAMETER_NAME: GGXF.GGXF_PARAMETER_DISPLACEMENT_NORTH,
        GGXF.PARAM_ATTR_UNIT_SI_RATIO: 1.0,
        GGXF.PARAM_ATTR_LENGTH_UNIT: "meter",
    },
    {
        GGXF.PARAM_ATTR_PARAMETER_NAME: GGXF.GGXF_PARAMETER_DISPLACEMENT_UP,
        GGXF.PARAM_ATTR_UNIT_SI_RATIO: 1.0,
        GGXF.PARAM_ATTR_LENGTH_UNIT: "meter",
    },
]


def dummyGGXF():
    metadata = {
        GGXF.GGXF_ATTR_CONTENT: GGXF.GGXF_CONTENT_DEFORMATION_MODEL,
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
        GGXF.GROUP_ATTR_PARAMETERS: gparams,
    }
    return GGXF.Group(dummyGGXF(), "DummyGroup", metadata)
