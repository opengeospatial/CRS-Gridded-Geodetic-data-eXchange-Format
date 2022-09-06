# GGXF content types

from .Constants import *

CommonAttributes = {
    ATTRDEF_TYPE_GGXF: [
        {
            ATTRDEF_NAME: GGXF_ATTR_GGXF_VERSION,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_GGXF_VERSION,
                    ATTRDEF_TYPE: [GGXF_VERSION_G_G_X_F_1_0],
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_CONTENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_CONTENT,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_TITLE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_TITLE,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_ABSTRACT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_ABSTRACT,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_FILENAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_FILENAME,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_CONTENT_APPLICABILITY_EXTENT,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_EXTENTS,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_CONTENT_BOX,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_CONTENT_BOX,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_BOUNDING_BOX,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_PARAMETERS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_PARAMETERS,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_PARAMETER,
                    ATTRDEF_LIST: True,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_INTERPOLATION_CRS_WKT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_INTERPOLATION_CRS_WKT,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_SOURCE_CRS_WKT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_SOURCE_CRS_WKT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_TARGET_CRS_WKT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_TARGET_CRS_WKT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_LICENSE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_LICENSE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_OPERATION_ACCURACY,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_OPERATION_ACCURACY,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_PUBLICATION_DATE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_PUBLICATION_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_VERSION,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_VERSION,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_DIGITAL_OBJECT_IDENTIFIER,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_DIGITAL_OBJECT_IDENTIFIER,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_PARTY_NAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_PARTY_NAME,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_ELECTRONIC_MAIL_ADDRESS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_ELECTRONIC_MAIL_ADDRESS,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_ONLINE_RESOURCE_LINKAGE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_ONLINE_RESOURCE_LINKAGE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_DELIVERY_POINT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_DELIVERY_POINT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_COMMENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_COMMENT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_TIDE_SYSTEM,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_TIDE_SYSTEM,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_USER_DEFINED_METHOD_EXAMPLE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_USER_DEFINED_METHOD_EXAMPLE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_USER_DEFINED_METHOD_FORMULA,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_USER_DEFINED_METHOD_FORMULA,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_USER_DEFINED_METHOD_FORMULA_CITATION,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_USER_DEFINED_METHOD_FORMULA_CITATION,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
    ATTRDEF_TYPE_GROUP: [
        {
            ATTRDEF_NAME: GROUP_ATTR_GROUP_PARAMETERS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_GROUP_PARAMETERS,
                    ATTRDEF_TYPE: str,
                    ATTRDEF_LIST: True,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GROUP_ATTR_GROUP_DEFAULT_VALUES,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_GROUP_DEFAULT_VALUES,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_PARAMETER_DEFAULT_VALUE,
                    ATTRDEF_LIST: True,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GROUP_ATTR_INTERPOLATION_METHOD,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_INTERPOLATION_METHOD,
                    ATTRDEF_TYPE: [
                        INTERPOLATION_METHOD_BILINEAR,
                        INTERPOLATION_METHOD_BICUBIC,
                        INTERPOLATION_METHOD_BIQUADRATIC,
                    ],
                },
            ],
        },
        {
            ATTRDEF_NAME: GROUP_ATTR_INTERPOLATION_METHOD_CITATION,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_INTERPOLATION_METHOD_CITATION,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GROUP_ATTR_COMMENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_COMMENT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
    ATTRDEF_TYPE_GRID: [
        {
            ATTRDEF_NAME: GRID_ATTR_I_NODE_COUNT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_I_NODE_COUNT,
                    ATTRDEF_TYPE: int,
                },
            ],
        },
        {
            ATTRDEF_NAME: GRID_ATTR_J_NODE_COUNT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_J_NODE_COUNT,
                    ATTRDEF_TYPE: int,
                },
            ],
        },
        {
            ATTRDEF_NAME: GRID_ATTR_K_NODE_COUNT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_K_NODE_COUNT,
                    ATTRDEF_TYPE: int,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GRID_ATTR_GRID_PRIORITY,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_GRID_PRIORITY,
                    ATTRDEF_TYPE: int,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GRID_ATTR_AFFINE_COEFFS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_AFFINE_COEFFS,
                    ATTRDEF_TYPE: float,
                    ATTRDEF_LIST: True,
                    ATTRDEF_COUNT: 6,
                },
            ],
        },
        {
            ATTRDEF_NAME: GRID_ATTR_COMMENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_COMMENT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
    ATTRDEF_TYPE_PARAMETER: [
        {
            ATTRDEF_NAME: PARAM_ATTR_PARAMETER_NAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_PARAMETER_NAME,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_PARAMETER_SET,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_PARAMETER_SET,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_UNIT_SI_RATIO,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_UNIT_SI_RATIO,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_UNIT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_UNIT,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_SOURCE_CRS_AXIS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_SOURCE_CRS_AXIS,
                    ATTRDEF_TYPE: int,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_PARAMETER_MINIMUM_VALUE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_PARAMETER_MINIMUM_VALUE,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_PARAMETER_MAXIMUM_VALUE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_PARAMETER_MAXIMUM_VALUE,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_NO_DATA_FLAG,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_NO_DATA_FLAG,
                    ATTRDEF_TYPE: None,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_UNCERTAINTY_MEASURE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_UNCERTAINTY_MEASURE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: PARAM_ATTR_DEFAULT_VALUE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: PARAM_ATTR_DEFAULT_VALUE,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
    ATTRDEF_TYPE_PARAMETER_DEFAULT_VALUE: [
        {
            ATTRDEF_NAME: GGXF_ATTR_PARAMETER_NAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_PARAMETER_NAME,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_DEFAULT_VALUE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_DEFAULT_VALUE,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
    ],
    ATTRDEF_TYPE_EXTENTS: [
        {
            ATTRDEF_NAME: GGXF_ATTR_BOUNDING_BOX,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_BOUNDING_BOX,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_BOUNDING_BOX,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_EXTENT_DESCRIPTION,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_EXTENT_DESCRIPTION,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_BOUNDING_POLYGON,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_BOUNDING_POLYGON,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_TEMPORAL_EXTENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_TEMPORAL_EXTENT,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_TEMPORAL_EXTENT,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_VERTICAL_EXTENT,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
    ATTRDEF_TYPE_BOUNDING_BOX: [
        {
            ATTRDEF_NAME: GGXF_ATTR_SOUTH_BOUND_LATITUDE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_SOUTH_BOUND_LATITUDE,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_WEST_BOUND_LONGITUDE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_WEST_BOUND_LONGITUDE,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_NORTH_BOUND_LATITUDE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_NORTH_BOUND_LATITUDE,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_EAST_BOUND_LONGITUDE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_EAST_BOUND_LONGITUDE,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
    ],
    ATTRDEF_TYPE_TEMPORAL_EXTENT: [
        {
            ATTRDEF_NAME: GGXF_ATTR_START_DATE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_START_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_END_DATE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_END_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
    ],
    ATTRDEF_TYPE_VERTICAL_EXTENT: [
        {
            ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT_CRS_WKT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT_CRS_WKT,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT_MINIMUM,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT_MINIMUM,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT_MAXIMUM,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_VERTICAL_EXTENT_MAXIMUM,
                    ATTRDEF_TYPE: float,
                },
            ],
        },
    ],
    ATTRDEF_TYPE_TIME_FUNCTION: [
        {
            ATTRDEF_NAME: TIME_PARAM_FUNCTION_TYPE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_FUNCTION_TYPE,
                    ATTRDEF_TYPE: [
                        TIME_FUNCTION_TYPE_VELOCITY,
                        TIME_FUNCTION_TYPE_STEP,
                        TIME_FUNCTION_TYPE_RAMP,
                        TIME_FUNCTION_TYPE_ACCELERATION,
                        TIME_FUNCTION_TYPE_EXPONENTIAL,
                        TIME_FUNCTION_TYPE_LOGARITHMIC,
                        TIME_FUNCTION_TYPE_HYPERBOLIC_TANGENT,
                        TIME_FUNCTION_TYPE_CYCLIC,
                    ],
                },
            ],
        },
        {
            ATTRDEF_NAME: TIME_PARAM_START_EPOCH,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_START_EPOCH,
                    ATTRDEF_TYPE: float,
                },
                {
                    ATTRDEF_NAME: TIME_PARAM_START_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: TIME_PARAM_END_EPOCH,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_END_EPOCH,
                    ATTRDEF_TYPE: float,
                },
                {
                    ATTRDEF_NAME: TIME_PARAM_END_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: TIME_PARAM_FUNCTION_REFERENCE_EPOCH,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_FUNCTION_REFERENCE_EPOCH,
                    ATTRDEF_TYPE: float,
                },
                {
                    ATTRDEF_NAME: TIME_PARAM_FUNCTION_REFERENCE_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: TIME_PARAM_EVENT_EPOCH,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_EVENT_EPOCH,
                    ATTRDEF_TYPE: float,
                },
                {
                    ATTRDEF_NAME: TIME_PARAM_EVENT_DATE,
                    ATTRDEF_TYPE: str,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: TIME_PARAM_SCALE_FACTOR,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_SCALE_FACTOR,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: TIME_PARAM_TIME_CONSTANT,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_TIME_CONSTANT,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: TIME_PARAM_FREQUENCY,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: TIME_PARAM_FREQUENCY,
                    ATTRDEF_TYPE: float,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
}

YamlAttributes = {
    ATTRDEF_TYPE_GGXF: [
        {
            ATTRDEF_NAME: GGXF_ATTR_GGXF_GROUPS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_GGXF_GROUPS,
                    ATTRDEF_TYPE: None,
                    ATTRDEF_LIST: True,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_GRID_DATA,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_GRID_DATA,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_YAML_GRID_DATA,
                    ATTRDEF_LIST: True,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
    ],
    ATTRDEF_TYPE_GROUP: [
        {
            ATTRDEF_NAME: GROUP_ATTR_GGXF_GROUP_NAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_GGXF_GROUP_NAME,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_UNICODE_IDENTIFIER,
                },
            ],
        },
        {
            ATTRDEF_NAME: GROUP_ATTR_GRIDS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_GRIDS,
                    ATTRDEF_TYPE: None,
                    ATTRDEF_LIST: True,
                },
            ],
        },
    ],
    ATTRDEF_TYPE_GRID: [
        {
            ATTRDEF_NAME: GRID_ATTR_GRID_NAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_GRID_NAME,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_UNICODE_IDENTIFIER,
                },
            ],
        },
        {
            ATTRDEF_NAME: GRID_ATTR_GRIDS,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_GRIDS,
                    ATTRDEF_TYPE: None,
                    ATTRDEF_LIST: True,
                },
            ],
            ATTRDEF_OPTIONAL: True,
        },
        {
            ATTRDEF_NAME: GRID_ATTR_DATA_SOURCE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GRID_ATTR_DATA,
                    ATTRDEF_TYPE: None,
                },
                {
                    ATTRDEF_NAME: GRID_ATTR_DATA_SOURCE,
                    ATTRDEF_TYPE: dict,
                },
            ],
        },
    ],
    ATTRDEF_TYPE_YAML_GRID_DATA: [
        {
            ATTRDEF_NAME: GGXF_ATTR_GRID_NAME,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_GRID_NAME,
                    ATTRDEF_TYPE: ATTRDEF_TYPE_UNICODE_IDENTIFIER,
                },
            ],
        },
        {
            ATTRDEF_NAME: GGXF_ATTR_DATA_SOURCE,
            ATTRDEF_CHOICE: [
                {
                    ATTRDEF_NAME: GGXF_ATTR_DATA,
                    ATTRDEF_TYPE: None,
                },
                {
                    ATTRDEF_NAME: GGXF_ATTR_DATA_SOURCE,
                    ATTRDEF_TYPE: str,
                },
            ],
        },
    ],
}

ContentTypes = {
    GGXF_CONTENT_CARTESIAN_2D_OFFSETS: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_EASTING_OFFSET, GGXF_PARAMETER_NORTHING_OFFSET},
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY,
            },
            {GGXF_PARAMETER_WESTING_OFFSET, GGXF_PARAMETER_NORTHING_OFFSET},
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY,
            },
            {GGXF_PARAMETER_EASTING_OFFSET, GGXF_PARAMETER_SOUTHING_OFFSET},
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY,
            },
            {GGXF_PARAMETER_WESTING_OFFSET, GGXF_PARAMETER_SOUTHING_OFFSET},
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_EASTING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_NORTHING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_SOUTHING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_WESTING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_CARTESIAN_3D_OFFSETS: {
        ATTRDEF_PARAMETER_SETS: [
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
                GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
                GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
                GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_HEIGHT_OFFSET,
                GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
                GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_NORTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
                GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
            },
            {
                GGXF_PARAMETER_EASTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
                GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
            },
            {
                GGXF_PARAMETER_WESTING_OFFSET,
                GGXF_PARAMETER_SOUTHING_OFFSET,
                GGXF_PARAMETER_DEPTH_OFFSET,
                GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_DEPTH_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_EASTING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_EASTING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_HEIGHT_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_NORTHING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_NORTHING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_SOUTHING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_SOUTHING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_WESTING_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_WESTING_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_GEOCENTRIC_TRANSLATIONS: {
        ATTRDEF_PARAMETER_SETS: [
            {
                GGXF_PARAMETER_GEOCENTRIC_X_OFFSET,
                GGXF_PARAMETER_GEOCENTRIC_Y_OFFSET,
                GGXF_PARAMETER_GEOCENTRIC_Z_OFFSET,
            },
            {
                GGXF_PARAMETER_GEOCENTRIC_X_OFFSET,
                GGXF_PARAMETER_GEOCENTRIC_Y_OFFSET,
                GGXF_PARAMETER_GEOCENTRIC_Z_OFFSET,
                GGXF_PARAMETER_GEOCENTRIC_X_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_GEOCENTRIC_Y_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_GEOCENTRIC_Z_OFFSET_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_GEOCENTRIC_X_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_GEOCENTRIC_X_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_GEOCENTRIC_Y_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_GEOCENTRIC_Y_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_GEOCENTRIC_Z_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_GEOCENTRIC_Z_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_GEOGRAPHIC_2D_OFFSETS: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_LATITUDE_OFFSET, GGXF_PARAMETER_LONGITUDE_OFFSET},
            {
                GGXF_PARAMETER_LATITUDE_OFFSET,
                GGXF_PARAMETER_LONGITUDE_OFFSET,
                GGXF_PARAMETER_LATITUDE_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_LONGITUDE_OFFSET_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_LATITUDE_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_LATITUDE_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_LONGITUDE_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_LONGITUDE_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_GEOGRAPHIC_3D_OFFSETS: {
        ATTRDEF_PARAMETER_SETS: [
            {
                GGXF_PARAMETER_LATITUDE_OFFSET,
                GGXF_PARAMETER_LONGITUDE_OFFSET,
                GGXF_PARAMETER_ELLIPSOIDAL_HEIGHT_OFFSET,
            },
            {
                GGXF_PARAMETER_LATITUDE_OFFSET,
                GGXF_PARAMETER_LONGITUDE_OFFSET,
                GGXF_PARAMETER_ELLIPSOIDAL_HEIGHT_OFFSET,
                GGXF_PARAMETER_LATITUDE_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_LONGITUDE_OFFSET_UNCERTAINTY,
                GGXF_PARAMETER_ELLIPSOIDAL_HEIGHT_OFFSET_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_ELLIPSOIDAL_HEIGHT_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_ELLIPSOIDAL_HEIGHT_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_LATITUDE_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_LATITUDE_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_LONGITUDE_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_LONGITUDE_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_VERTICAL_OFFSETS: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_HEIGHT_OFFSET},
            {GGXF_PARAMETER_HEIGHT_OFFSET, GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY},
            {GGXF_PARAMETER_DEPTH_OFFSET},
            {GGXF_PARAMETER_DEPTH_OFFSET, GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY},
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_DEPTH_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_DEPTH_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
            GGXF_PARAMETER_HEIGHT_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_GEOID_MODEL: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_GEOID_HEIGHT},
            {GGXF_PARAMETER_GEOID_HEIGHT, GGXF_PARAMETER_GEOID_HEIGHT_UNCERTAINTY},
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_GEOID_HEIGHT: GGXF_PARAMETER_SET_GEOID_HEIGHT,
            GGXF_PARAMETER_GEOID_HEIGHT_UNCERTAINTY: GGXF_PARAMETER_SET_GEOID_HEIGHT_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_DEVIATIONS_OF_THE_VERTICAL: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_DEVIATION_EAST, GGXF_PARAMETER_DEVIATION_NORTH},
            {
                GGXF_PARAMETER_DEVIATION_EAST,
                GGXF_PARAMETER_DEVIATION_NORTH,
                GGXF_PARAMETER_DEVIATION_EAST_UNCERTAINTY,
                GGXF_PARAMETER_DEVIATION_NORTH_UNCERTAINTY,
            },
            {GGXF_PARAMETER_DEVIATION_EAST_GEOID, GGXF_PARAMETER_DEVIATION_NORTH_GEOID},
            {
                GGXF_PARAMETER_DEVIATION_EAST_GEOID,
                GGXF_PARAMETER_DEVIATION_NORTH_GEOID,
                GGXF_PARAMETER_DEVIATION_EAST_GEOID_UNCERTAINTY,
                GGXF_PARAMETER_DEVIATION_NORTH_GEOID_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_DEVIATION_EAST: GGXF_PARAMETER_SET_DEVIATION,
            GGXF_PARAMETER_DEVIATION_EAST_GEOID: GGXF_PARAMETER_SET_DEVIATION,
            GGXF_PARAMETER_DEVIATION_EAST_GEOID_UNCERTAINTY: GGXF_PARAMETER_SET_DEVIATION_UNCERTAINTY,
            GGXF_PARAMETER_DEVIATION_EAST_UNCERTAINTY: GGXF_PARAMETER_SET_DEVIATION_UNCERTAINTY,
            GGXF_PARAMETER_DEVIATION_NORTH: GGXF_PARAMETER_SET_DEVIATION,
            GGXF_PARAMETER_DEVIATION_NORTH_GEOID: GGXF_PARAMETER_SET_DEVIATION,
            GGXF_PARAMETER_DEVIATION_NORTH_GEOID_UNCERTAINTY: GGXF_PARAMETER_SET_DEVIATION_UNCERTAINTY,
            GGXF_PARAMETER_DEVIATION_NORTH_UNCERTAINTY: GGXF_PARAMETER_SET_DEVIATION_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_HYDROID_MODEL: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_HEIGHT_OFFSET},
            {GGXF_PARAMETER_HEIGHT_OFFSET, GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY},
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_HEIGHT_OFFSET: GGXF_PARAMETER_SET_OFFSET,
            GGXF_PARAMETER_HEIGHT_OFFSET_UNCERTAINTY: GGXF_PARAMETER_SET_OFFSET_UNCERTAINTY,
        },
        ATTRDEF_ATTRIBUTES: {
            ATTRDEF_TYPE_GROUP: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_TIDAL_SURFACE,
                    ATTRDEF_CHOICE: [
                        {
                            ATTRDEF_NAME: GROUP_ATTR_TIDAL_SURFACE,
                            ATTRDEF_TYPE: [
                                TIDAL_SURFACE_C_D,
                                TIDAL_SURFACE_H_A_T,
                                TIDAL_SURFACE_H_W,
                                TIDAL_SURFACE_H_H_W_L_T,
                                TIDAL_SURFACE_I_S_L_W,
                                TIDAL_SURFACE_L_A_T,
                                TIDAL_SURFACE_L_W,
                                TIDAL_SURFACE_L_L_W_L_T,
                                TIDAL_SURFACE_M_H_H_W,
                                TIDAL_SURFACE_M_H_W,
                                TIDAL_SURFACE_M_H_W_S_T,
                                TIDAL_SURFACE_M_L_L_W,
                                TIDAL_SURFACE_M_L_W,
                                TIDAL_SURFACE_M_L_W_S_T,
                                TIDAL_SURFACE_M_L_L_W_S_T,
                                TIDAL_SURFACE_M_S_L,
                            ],
                        },
                    ],
                },
            ],
        },
    },
    GGXF_CONTENT_VELOCITY_MODEL: {
        ATTRDEF_PARAMETER_SETS: [
            {GGXF_PARAMETER_VELOCITY_EAST, GGXF_PARAMETER_VELOCITY_NORTH},
            {
                GGXF_PARAMETER_VELOCITY_EAST,
                GGXF_PARAMETER_VELOCITY_NORTH,
                GGXF_PARAMETER_VELOCITY_EAST_UNCERTAINTY,
                GGXF_PARAMETER_VELOCITY_NORTH_UNCERTAINTY,
            },
            {
                GGXF_PARAMETER_VELOCITY_EAST,
                GGXF_PARAMETER_VELOCITY_NORTH,
                GGXF_PARAMETER_VELOCITY_UP,
            },
            {
                GGXF_PARAMETER_VELOCITY_EAST,
                GGXF_PARAMETER_VELOCITY_NORTH,
                GGXF_PARAMETER_VELOCITY_UP,
                GGXF_PARAMETER_VELOCITY_EAST_UNCERTAINTY,
                GGXF_PARAMETER_VELOCITY_NORTH_UNCERTAINTY,
                GGXF_PARAMETER_VELOCITY_UP_UNCERTAINTY,
            },
            {GGXF_PARAMETER_VELOCITY_UP},
            {GGXF_PARAMETER_VELOCITY_UP, GGXF_PARAMETER_VELOCITY_UP_UNCERTAINTY},
            {
                GGXF_PARAMETER_VELOCITY_X,
                GGXF_PARAMETER_VELOCITY_Y,
                GGXF_PARAMETER_VELOCITY_Z,
            },
            {
                GGXF_PARAMETER_VELOCITY_X,
                GGXF_PARAMETER_VELOCITY_Y,
                GGXF_PARAMETER_VELOCITY_Z,
                GGXF_PARAMETER_VELOCITY_X_UNCERTAINTY,
                GGXF_PARAMETER_VELOCITY_Y_UNCERTAINTY,
                GGXF_PARAMETER_VELOCITY_Z_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_VELOCITY_EAST: GGXF_PARAMETER_SET_VELOCITY,
            GGXF_PARAMETER_VELOCITY_EAST_UNCERTAINTY: GGXF_PARAMETER_SET_VELOCITY_UNCERTAINTY,
            GGXF_PARAMETER_VELOCITY_NORTH: GGXF_PARAMETER_SET_VELOCITY,
            GGXF_PARAMETER_VELOCITY_NORTH_UNCERTAINTY: GGXF_PARAMETER_SET_VELOCITY_UNCERTAINTY,
            GGXF_PARAMETER_VELOCITY_UP: GGXF_PARAMETER_SET_VELOCITY,
            GGXF_PARAMETER_VELOCITY_UP_UNCERTAINTY: GGXF_PARAMETER_SET_VELOCITY_UNCERTAINTY,
            GGXF_PARAMETER_VELOCITY_X: GGXF_PARAMETER_SET_VELOCITY,
            GGXF_PARAMETER_VELOCITY_X_UNCERTAINTY: GGXF_PARAMETER_SET_VELOCITY_UNCERTAINTY,
            GGXF_PARAMETER_VELOCITY_Y: GGXF_PARAMETER_SET_VELOCITY,
            GGXF_PARAMETER_VELOCITY_Y_UNCERTAINTY: GGXF_PARAMETER_SET_VELOCITY_UNCERTAINTY,
            GGXF_PARAMETER_VELOCITY_Z: GGXF_PARAMETER_SET_VELOCITY,
            GGXF_PARAMETER_VELOCITY_Z_UNCERTAINTY: GGXF_PARAMETER_SET_VELOCITY_UNCERTAINTY,
        },
    },
    GGXF_CONTENT_DEFORMATION_MODEL: {
        ATTRDEF_PARAMETER_SETS: [
            {
                GGXF_PARAMETER_DISPLACEMENT_EAST,
                GGXF_PARAMETER_DISPLACEMENT_NORTH,
                GGXF_PARAMETER_DISPLACEMENT_UP,
            },
            {
                GGXF_PARAMETER_DISPLACEMENT_EAST,
                GGXF_PARAMETER_DISPLACEMENT_NORTH,
                GGXF_PARAMETER_DISPLACEMENT_UP,
                GGXF_PARAMETER_HORIZONTAL_DISPLACEMENT_UNCERTAINTY,
                GGXF_PARAMETER_VERTICAL_DISPLACEMENT_UNCERTAINTY,
            },
            {GGXF_PARAMETER_DISPLACEMENT_EAST, GGXF_PARAMETER_DISPLACEMENT_NORTH},
            {
                GGXF_PARAMETER_DISPLACEMENT_EAST,
                GGXF_PARAMETER_DISPLACEMENT_NORTH,
                GGXF_PARAMETER_HORIZONTAL_DISPLACEMENT_UNCERTAINTY,
            },
            {GGXF_PARAMETER_DISPLACEMENT_UP},
            {
                GGXF_PARAMETER_DISPLACEMENT_UP,
                GGXF_PARAMETER_VERTICAL_DISPLACEMENT_UNCERTAINTY,
            },
        ],
        ATTRDEF_PARAMSET_MAP: {
            GGXF_PARAMETER_DISPLACEMENT_EAST: GGXF_PARAMETER_SET_DISPLACEMENT,
            GGXF_PARAMETER_DISPLACEMENT_NORTH: GGXF_PARAMETER_SET_DISPLACEMENT,
            GGXF_PARAMETER_DISPLACEMENT_UP: GGXF_PARAMETER_SET_DISPLACEMENT,
            GGXF_PARAMETER_HORIZONTAL_DISPLACEMENT_UNCERTAINTY: GGXF_PARAMETER_SET_DISPLACEMENT_UNCERTAINTY,
            GGXF_PARAMETER_VERTICAL_DISPLACEMENT_UNCERTAINTY: GGXF_PARAMETER_SET_DISPLACEMENT_UNCERTAINTY,
        },
        ATTRDEF_ATTRIBUTES: {
            ATTRDEF_TYPE_GROUP: [
                {
                    ATTRDEF_NAME: GROUP_ATTR_TIME_FUNCTIONS,
                    ATTRDEF_CHOICE: [
                        {
                            ATTRDEF_NAME: GROUP_ATTR_TIME_FUNCTIONS,
                            ATTRDEF_TYPE: None,
                            ATTRDEF_LIST: True,
                        },
                    ],
                },
            ],
        },
    },
}
