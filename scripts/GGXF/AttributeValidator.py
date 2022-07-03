from re import S
from .Constants import *
from .GGXF_Types import ContentTypes
from collections import namedtuple
import re


class AttributeValidator:
    class Error(RuntimeError):
        pass

    class ValidationError(RuntimeError):
        pass

    AttributeDef = namedtuple("AttributeDef", "name atype islist count")

    #    StringTypes = {"UnicodeIdentifier": lambda s: re.match(r"^[a-z]\w+$", s, re.I)}
    StringTypes = {"UnicodeIdentifier": lambda s: not re.search(r"^[a-z_][^\S\/]*$", s)}

    class AttributeChoice:
        """
        Identifies a list of alternative attributes.  Most attributes only have one choice
        but this provides generality for eg eventDate or eventEpoch.  Each attribute is of type
        AttributeDef providing name, atype, islist, and count.  Count is used if islist is True,
        if it is not zero then the list must have this many values.
        """

        def __init__(self, choicedef: dict):
            try:
                self._name = choicedef[ATTRDEF_NAME]
                self._attrdefs = []
                for attrdef in choicedef[ATTRDEF_CHOICE]:
                    name = attrdef[ATTRDEF_NAME]
                    atype = attrdef[ATTRDEF_TYPE]
                    islist = attrdef.get(ATTRDEF_LIST, False)
                    count = attrdef.get(ATTRDEF_COUNT)
                    self._attrdefs.append(
                        AttributeValidator.AttributeDef(name, atype, islist, count)
                    )
                self._optional = bool(choicedef.get("Optional", False))
            except Exception as ex:
                raise AttributeValidator.Error(
                    f"Error loading attribute definition {choicedef.get('Name','unnamed')}: {ex}"
                )

        def name(self):
            return self._name

        def definitions(self):
            return self._attrdefs

        def update(self, attrdef):
            self._type = attrdef._type
            self._optional = attrdef._optional

        def validate(self, attributes: dict, context, validator):
            adef = None
            valid = True
            for attrdef in self._attrdefs:
                if attrdef.name in attributes:
                    if adef is not None:
                        validator.error(
                            f"{context}: Attributes {adef.name} and {attrdef.name} cannot both be defined"
                        )
                        return False
                    adef = attrdef

            if adef is None:
                if not self._optional:
                    names = " or ".join((a.name for a in self._attrdefs))
                    validator.error(f"{context}: Attribute {names} must be defined")
                    return False
                return valid
            values = attributes[adef.name]
            if adef.islist:
                if type(values) != list:
                    validator.error(
                        f"{context}: Attribute {adef.name} must be a list of values"
                    )
                    return False

                if len(values) == 0 and not self._optional:
                    validator.error(f"{context}: Attribute {adef.name} has no values")
                    return False
                if adef.count and len(values) != adef.count:
                    validator.error(
                        f"{context}: Attribute {adef.name} has the wrong number of items ({len(values)} instead of {adef.count})"
                    )
                    return False
            else:
                values = [values]
            for ivalue, value in enumerate(values):
                if adef.atype is None:
                    continue
                elif type(adef.atype) == list:
                    if value not in adef.atype:
                        validator.error(
                            f"{context}: Attribute value {value} is not valid for {adef.name}"
                        )
                        valid = False
                elif isinstance(adef.atype, type) and not isinstance(value, adef.atype):
                    if adef.atype == float and isinstance(value, int):
                        pass
                    else:
                        validator.error(
                            f"{context}: Attribute {adef.name} has the wrong type - must be {adef.atype.__name__}"
                        )
                        valid = False
                elif (
                    type(adef.atype) == str
                    and adef.atype in AttributeValidator.StringTypes
                ):
                    if type(value) != str:
                        validator.error(
                            f"{context}: Attribute {adef.name} is not a string"
                        )
                        valid = False
                    else:
                        testfunc = AttributeValidator.StringTypes[adef.atype]
                        if not testfunc(value):
                            validator.error(
                                f'{context}: Attribute {adef.name} value "{value}" is not a valid {adef.atype}'
                            )
                            valid = False
                elif type(adef.atype) == str:
                    if type(value) != dict:
                        validator.error(
                            f"{context}: Attribute {adef.name} doesn't have attributes of an {adef.atype} type"
                        )
                        valid = False
                    else:
                        vcontext = f"{context}: {adef.name}"
                        if adef.islist:
                            vcontext = vcontext + f"[{ivalue}]"

                        valid = valid and validator.validate(
                            value, adef.atype, vcontext
                        )
            return valid

    class TypeDefinition:
        def __init__(self, definitions: list = []):
            self._defs = {}
            self._attributeNames = set()
            self.update(definitions)

        def update(self, definitions: list):
            for definition in definitions:
                attrdef = AttributeValidator.AttributeChoice(definition)
                name = attrdef.name()
                if name in self._defs:
                    self._defs[name].update(definition)
                else:
                    self._defs[name] = attrdef
            names = set()
            for attrdef in self._defs.values():
                for attr in attrdef.definitions():
                    names.add(attr.name)
            self._attributeNames = names

        def validate(self, attributes: dict, context, validator):
            valid = True
            for attrdef in self._defs.values():
                valid = valid and attrdef.validate(attributes, context, validator)
            for attrname in attributes.keys():
                if attrname not in self._attributeNames:
                    validator.warn(f"{context}: Non-standard attribute {attrname}")

            return valid

    def __init__(self, typedefs: dict, errorhandler=None):
        self._typedefs = {}
        self._errorhandler = errorhandler
        self.update(typedefs)

    def update(self, typedefs: dict):
        for objtype, objdef in typedefs.items():
            typedef = self.typeDefinition(objtype)
            typedef.update(objdef)

    def error(self, message):
        if self._errorhandler:
            self._errorhandler.error(message)
        else:
            raise self.ValidationError(message)

    def warn(self, message):
        if self._errorhandler:
            self._errorhandler.warn(message)

    def typeDefinition(self, objtype):
        if objtype not in self._typedefs:
            self._typedefs[objtype] = AttributeValidator.TypeDefinition()
        return self._typedefs[objtype]

    def validate(self, attributes, objtype, context=None):
        if objtype not in self._typedefs:
            self.error(f"Cannot validate object of type {objtype}")
            return False
        context = context or objtype
        validationSet = self.typeDefinition(objtype)
        return validationSet.validate(attributes, context, self)

    def validateRootAttributes(self, attributes, context="GGXF"):
        ok = self.validate(attributes, ATTRDEF_TYPE_GGXF, context)
        if ok:
            contentType = attributes[GGXF_ATTR_CONTENT]
            if contentType not in ContentTypes:
                self.error(f"Invalid content type {contentType} for GGXF")
            else:
                self.update(ContentTypes[contentType].get(ATTRDEF_ATTRIBUTES, {}))
        return ok

    def validateGroupAttributes(self, attributes, context="Group"):
        ok = self.validate(attributes, ATTRDEF_TYPE_GROUP, context)
        return ok

    def validateGridAttributes(self, attributes, context="Grid"):
        ok = self.validate(attributes, ATTRDEF_TYPE_GRID, context)
        return ok
