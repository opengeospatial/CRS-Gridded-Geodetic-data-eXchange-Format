from .Constants import *
from .GGXF_Types import ContentTypes
from collections import namedtuple


class AttributeValidator:
    class Error(RuntimeError):
        pass

    class ValidationError(RuntimeError):
        pass

    AttributeDef = namedtuple("AttributeDef", "name atype islist count")

    class AttributeChoice:
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

        def update(self, attrdef):
            self._type = attrdef._type
            self._optional = attrdef._optional

        def validate(self, attributes: dict, context, validator):
            adef = None
            valid = True
            for attrdef in self._attrdefs:
                if attrdef.name in attributes:
                    if adef is not None:
                        validator.handleError(
                            f"{context}: Attributes {adef.name} and {attrdef.name} cannot both be defined"
                        )
                        return False
                    adef = attrdef

            if adef is None:
                if not self._optional:
                    names = " or ".join((a.name for a in self._attrdefs))
                    validator.handleError(
                        f"{context}: Attribute {names} must be defined"
                    )
                    return False
                return valid
            values = attributes[adef.name]
            if adef.islist:
                if type(values) != list:
                    validator.handleError(
                        f"{context}: Attribute {adef.name} must be a list of values"
                    )
                    return False

                if len(values) == 0 and not self._optional:
                    validator.handleError(
                        f"{context}: Attribute {adef.name} has no values"
                    )
                    return False
                if adef.count and len(values) != adef.count:
                    validator.handleError(
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
                        validator.handleError(
                            f"{context}: Attribute value {value} is not valid for {adef.name}"
                        )
                        valid = False
                elif isinstance(adef.atype, type) and not isinstance(value, adef.atype):
                    if adef.atype == float and isinstance(value, int):
                        pass
                    else:
                        validator.handleError(
                            f"{context}: Attribute {adef.name} has the wrong type - must be {adef.atype.__name__}"
                        )
                        valid = False
                elif type(adef.atype) == str:
                    if type(value) != dict:
                        validator.handleError(
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
            self.update(definitions)

        def update(self, definitions: list):
            for definition in definitions:
                attrdef = AttributeValidator.AttributeChoice(definition)
                name = attrdef.name()
                if name in self._defs:
                    self._defs[name].update(definition)
                else:
                    self._defs[name] = attrdef

        def validate(self, attributes: dict, context, validator):
            valid = True
            for attrdef in self._defs.values():
                valid = valid and attrdef.validate(attributes, context, validator)
            return valid

    def __init__(self, typedefs: dict, errorhandler=None):
        self._typedefs = {}
        self._errorhandler = errorhandler
        self.update(typedefs)

    def update(self, typedefs: dict):
        for objtype, objdef in typedefs.items():
            typedef = self.typeDefinition(objtype)
            typedef.update(objdef)

    def handleError(self, message):
        if self._errorhandler:
            self._errorhandler(message)
        else:
            raise self.ValidationError(message)

    def typeDefinition(self, objtype):
        if objtype not in self._typedefs:
            self._typedefs[objtype] = AttributeValidator.TypeDefinition()
        return self._typedefs[objtype]

    def validate(self, attributes, objtype, context=None):
        if objtype not in self._typedefs:
            self.handleError("Cannot validate object of type {objtype}")
            return False
        context = context or objtype
        validationSet = self.typeDefinition(objtype)
        return validationSet.validate(attributes, context, self)

    def validateRootAttributes(self, attributes, context="GGXF"):
        ok = self.validate(attributes, ATTRDEF_TYPE_GGXF, context)
        if ok:
            contentType = attributes[GGXF_ATTR_CONTENT]
            if contentType not in ContentTypes:
                self.handleError("Invalid content type {contentType} for GGXF")
            else:
                self.update(ContentTypes[contentType].get(ATTRDEF_ATTRIBUTES, {}))
        return ok

    def validateGroupAttributes(self, attributes, context="Group"):
        ok = self.validate(attributes, ATTRDEF_TYPE_GROUP, context)
        return ok

    def validateGridAttributes(self, attributes, context="Grid"):
        ok = self.validate(attributes, ATTRDEF_TYPE_GRID, context)
        return ok