#!/usr/bin/python3
#
# Hacked together script to convert a schema YAML file to a Python source code.
# Generates two files:
#   Constants.py defines names for string contants
#   GGXF_Types.py defines attributes and parameters required for various GGXF content types
# This is a long way from a full schema validation, but provides some validation of GGXF attributes.

from sys import pycache_prefix
import yaml
import re

infile = "ggxf_schema.yaml"
typefile = "GGXF_Types.py"
constfile = "Constants.py"

contentTypePrefix = "GGXF_CONTENT_"
paramPrefix = "GGXF_PARAMETER_"

attributePrefix = {
    "GGXF": "GGXF_ATTR_",
    "Group": "GROUP_ATTR_",
    "Grid": "GRID_ATTR_",
    "Parameter": "PARAM_ATTR_",
    "TimeFunction": "TIME_PARAM_",
}
defaultAttrPrefix = "GGXF_ATTR_"

listVarPrefix = {"functionType": "TIME_FUNCTION_TYPE"}

# Constants not defined in "schema" file


timeFuncAttrPy = """
TimeDependentContentTypes = [
    GGXF_CONTENT_DEFORMATION_MODEL,
]
"""

attrdefs = {
    "ATTRDEF_ATTRIBUTES": "Attributes",
    "ATTRDEF_PARAMETER_SETS": "ParameterSets",
    "ATTRDEF_CHOICE": "Choice",
    "ATTRDEF_NAME": "Name",
    "ATTRDEF_TYPE": "Type",
    "ATTRDEF_OPTIONAL": "Optional",
    "ATTRDEF_LIST": "List",
    "ATTRDEF_COUNT": "Count",
}

ctypes = {}
params = {}
attrs = {}
listVars = {}
objecttypes = set()


def ucaseName(name):
    if name != "GGXF":
        name = re.sub(r"([a-zA-Z])(?=[A-Z0-9])", r"\1_", name)
        name = re.sub(r"[^\w]", "_", name)
    return name.upper()


def readAttributes(source):
    global ggxfAttrs, groupAttgrs, gridAttrs, listVars
    attributes = {}
    usedtypes = set()
    basetypes = ("int", "float", "str", "dict", "any")
    for objtype in source:
        aprefix = attributePrefix.get(objtype, defaultAttrPrefix)
        if aprefix not in attrs:
            attrs[aprefix] = {}
        attrlist = source.get(objtype)
        try:
            context = attrlist
            typeattrs = []
            for attr in attrlist:
                context = attr
                optional = bool(attr.pop("Optional", False))
                if "AttributeChoice" in attr:
                    choice = attr.get("AttributeChoice")
                else:
                    choice = {
                        "AttributeChoiceName": attr["AttributeName"],
                        "Attributes": [attr],
                    }
                choicenamestr = choice.get("AttributeChoiceName")
                choicename = f"{aprefix}{ucaseName(choicenamestr)}"
                attrs[aprefix][choicename] = choicenamestr
                typedefs = []
                for attrdef in choice["Attributes"]:
                    context = attrdef
                    namestr = attrdef.get("AttributeName")
                    name = f"{aprefix}{ucaseName(namestr)}"
                    attrs[aprefix][name] = namestr
                    atype = attrdef.get("Type")
                    qualifiers = {}
                    choicetype = False
                    if type(atype) == list:
                        listname = listVarPrefix.get(namestr, ucaseName(namestr))
                        if listname not in listVars:
                            listVars[listname] = {}
                        typevals = []
                        for value in atype:
                            value = str(value)
                            valname = f"{listname}_{ucaseName(value)}"
                            listVars[listname][valname] = value
                            typevals.append(valname)
                        atype = f"[{','.join(typevals)}]"
                        choicetype = True
                    elif atype.startswith("list"):
                        match = re.match(
                            r"^list(?:\(\s*(\w+)\s*(?:\,\s*(\d+)\s*)?\))?$", atype
                        )
                        if not match:
                            raise RuntimeError(f"Invalid attribute type {atype}")
                        atype = match.group(1) or "any"
                        qualifiers = {"ATTRDEF_LIST": True}
                        if match.group(2):
                            qualifiers["ATTRDEF_COUNT"] = int(match.group(2))
                    if atype not in basetypes and not choicetype:
                        usedtypes.add(atype)
                        atypeid = f"ATTRDEF_TYPE_{ucaseName(atype)}"
                        attrdefs[atypeid] = atype
                        atype = atypeid
                    elif atype == "any":
                        atype = None
                    typedef = {"ATTRDEF_NAME": name, "ATTRDEF_TYPE": atype}
                    typedef.update(qualifiers)
                    typedefs.append(typedef)
                choicedef = {"ATTRDEF_NAME": choicename, "ATTRDEF_CHOICE": typedefs}
                choicedef["ATTRDEF_OPTIONAL"] = optional
                typeattrs.append(choicedef)
            objtypeid = f"ATTRDEF_TYPE_{ucaseName(objtype)}"
            attrdefs[objtypeid] = objtype
            attributes[objtypeid] = typeattrs
            objecttypes.add(objtype)
        except Exception as ex:
            raise RuntimeError(f"Exception in {context}") from ex
    for objtype in usedtypes:
        if objtype not in objecttypes:
            raise RuntimeError(f"Undefined object type {objtype} in schema")
    return attributes


def writeAttributes(pyh, attributes, prefix):
    pyh.write("{\n")
    for objtypeid in attributes:
        pyh.write(f"{prefix}{objtypeid}: [\n")
        for attrdef in attributes[objtypeid]:
            pyh.write(f"{prefix}  {{\n")
            pyh.write(f"{prefix}    ATTRDEF_NAME: {attrdef['ATTRDEF_NAME']},\n")
            pyh.write(f"{prefix}    ATTRDEF_CHOICE: [\n")
            for attr in attrdef["ATTRDEF_CHOICE"]:
                pyh.write(f"{prefix}      {{\n")
                for key, value in attr.items():
                    pyh.write(f"{prefix}    {key}: {value},\n")
                pyh.write(f"{prefix}      }},\n")
            pyh.write(f"{prefix}      ],\n")
            if attrdef.get("ATTRDEF_OPTIONAL"):
                pyh.write(f"{prefix}    ATTRDEF_OPTIONAL: True,\n")
            pyh.write(f"{prefix}  }},\n")
        pyh.write(f"{prefix}  ],\n")
    pyh.write(f"{prefix}}}")


with open(infile) as yh, open(typefile, "w") as pyh:
    ggxftypes = yaml.load(yh, Loader=yaml.Loader)
    pyh.write("# GGXF content types\n\n")
    pyh.write("from .Constants import *\n")
    for attrlist in ("CommonAttributes", "YamlAttributes"):
        attributes = readAttributes(ggxftypes.get(attrlist, {}))
        pyh.write(f"\n{attrlist}=")
        writeAttributes(pyh, attributes, "  ")
        pyh.write("\n")

    pyh.write("\nContentTypes={\n")
    for cdata in ggxftypes["ContentTypes"]:
        ctypestr = cdata.get("ContentType")
        ctype = f"{contentTypePrefix}{ucaseName(ctypestr)}"
        ctypes[ctype] = ctypestr
        pyh.write(f"  {ctype}: {{\n    ATTRDEF_PARAMETER_SETS: [\n")
        for ps in cdata.get("ParameterSets", {}):
            psparams = {
                f"{paramPrefix}{ucaseName(p)}": p for p in ps.get("Parameters", [])
            }
            params.update(psparams)
            plistu = list(psparams.keys())
            plist = [p for p in plistu if not p.endswith("_UNCERTAINTY")]
            pyh.write(f"      [{','.join(plist)}],\n")
            if len(plistu) > len(plist):
                pyh.write(f"      [{','.join(plistu)}],\n")
        pyh.write(f"      ],\n")
        if "Attributes" in cdata:
            attributes = readAttributes(cdata["Attributes"])
            pyh.write("    ATTRDEF_ATTRIBUTES: ")
            writeAttributes(pyh, attributes, "      ")
            pyh.write(",\n")
        pyh.write("    },\n")
    pyh.write("  }\n")

with open("Constants.py", "w") as pyh:
    pyh.write("# GGXF constants\n\n")
    for varlist in (ctypes, params):
        for c in sorted(varlist):
            pyh.write(f"{c}={repr(varlist[c])}\n")
        pyh.write("\n")
    for objattr in attrs.values():
        for a in objattr:
            pyh.write(f"{a}={repr(objattr[a])}\n")
    pyh.write(timeFuncAttrPy)
    pyh.write("\n")
    for vtype in sorted(listVars):
        typevars = listVars[vtype]
        for v in sorted(typevars):
            pyh.write(f"{v}={repr(typevars[v])}\n")
    pyh.write("\n")
    for attrdef in attrdefs:
        pyh.write(f"{attrdef}={repr(attrdefs[attrdef])}\n")
