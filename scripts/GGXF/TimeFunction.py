#!/usr/bin/python3
#
#  Script to dump a single parameter from a single grid from a NetCDF4 XYZ file to an ASCII XYZ file

import datetime
import logging
import re
import math

import numpy as np
from .Constants import *


class Error(RuntimeError):
    pass


def DateToEpoch(sourcedate):
    # Parse a date and convert to an epoch (decimal year)

    if type(sourcedate) == float:
        return sourcedate
    if type(sourcedate) == str:
        match = re.match(
            r"^([12]\d\d\d)\-(\d\d)\-(\d\d)(?:T(\d\d)\:(\d\d)\:(\d\d)(?:\.\d+)?Z?)?$",
            sourcedate.strip(),
        )
        if not match:
            raise Error(f"Invalid date format {sourcedate}")
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4)) if match.group(4) else 0
        minute = int(match.group(5)) if match.group(5) else 0
        second = int(match.group(6)) if match.group(6) else 0
        sourcedate = datetime.datetime(year, month, day, hour, minute, second)
    if type(sourcedate == datetime.datetime or type(sourcedate) == datetime.date):
        year = sourcedate.year
        year0 = datetime.datetime(year, 1, 1)
        year1 = datetime.datetime(year + 1, 1, 1)
        return year + (
            (sourcedate - year0).total_seconds() / (year1 - year0).total_seconds()
        )
    raise Error(f"Invalide date {sourcedate}")


class BaseTimeFunction:
    @staticmethod
    def Create(definition: dict):
        constructors = {
            TIME_FUNCTION_TYPE_ACCELERATION: AccelerationTimeFunction,
            TIME_FUNCTION_TYPE_CYCLIC: CyclicTimeFunction,
            TIME_FUNCTION_TYPE_EXPONENTIAL: ExponentialTimeFunction,
            TIME_FUNCTION_TYPE_HYPERBOLIC_TANGENT: HyperbolicTangentTimeFunction,
            TIME_FUNCTION_TYPE_LOGARITHMIC: LogarithmicTimeFunction,
            TIME_FUNCTION_TYPE_RAMP: RampTimeFunction,
            TIME_FUNCTION_TYPE_STEP: StepTimeFunction,
            TIME_FUNCTION_TYPE_VELOCITY: VelocityTimeFunction,
        }
        if TIME_PARAM_FUNCTION_NAME not in definition:
            raise Error(
                f"Time function definition does not include {TIME_PARAM_FUNCTION_NAME}"
            )
        functionType = definition.get(TIME_PARAM_FUNCTION_NAME)
        if functionType not in constructors:
            raise Error(f"Unrecognized time function type {functionType}")
        return constructors[functionType](definition)

    OptionalParams = (
        TIME_PARAM_START_EPOCH,
        TIME_PARAM_END_EPOCH,
        TIME_PARAM_FUNCTION_REFERENCE_EPOCH,
        TIME_PARAM_SCALE_FACTOR,
    )

    def __init__(self, functiontype: str, definition: dict, required):
        self._params = {}
        for sourcekey, sourcevalue in definition.items():
            # Crudely handle option of Epoch or Date representation of times
            if sourcekey == TIME_PARAM_FUNCTION_NAME:
                continue
            key = sourcekey
            value = sourcevalue
            parser = float
            if key.endswith("Date"):
                key = key[:-4] + "Epoch"
                parser = DateToEpoch
            if key not in required and key not in self.OptionalParams:
                raise Error(
                    f"Unexpected parameter {sourcekey} in {functiontype} definition"
                )
            try:
                value = parser(sourcevalue)
            except:
                raise Error(
                    f"Invalid value {sourcevalue} for {sourcekey} in {functiontype} definition"
                )
            self._params[key] = value

        for key in required:
            if key not in self._params:
                raise Error(f"Missing value {key} in {functiontype} definition")

        self._refEpoch = self._params.get(TIME_PARAM_FUNCTION_REFERENCE_EPOCH)
        self._startEpoch = self._params.get(TIME_PARAM_START_EPOCH)
        self._endEpoch = self._params.get(TIME_PARAM_END_EPOCH)
        self._multiplier = self._params.get(TIME_PARAM_SCALE_FACTOR, 1.0)
        self._refValue = None

    def valueAt(self, epoch):
        if self._startEpoch and epoch < self._startEpoch:
            epoch = self._startEpoch
        elif self._endEpoch and epoch > self._endEpoch:
            epoch = self._endEpoch
        value = self.refFunc(epoch) * self._multiplier
        if self._refValue is None:
            self._refValue = 0.0
            if self._refEpoch is not None:
                self._refValue = self.valueAt(self._refEpoch)
        return value - self._refValue


class VelocityTimeFunction(BaseTimeFunction):

    Params = (TIME_PARAM_FUNCTION_REFERENCE_EPOCH,)

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_VELOCITY,
            definition,
            self.Params,
        )

    def refFunc(self, epoch):
        return epoch - self._refEpoch


class AccelerationTimeFunction:
    Params = (TIME_PARAM_FUNCTION_REFERENCE_EPOCH,)

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_ACCELERATION,
            definition,
            self.Params,
        )

    def refFunc(self, epoch):
        epoch -= self._refEpoch
        return epoch * epoch


class StepTimeFunction(BaseTimeFunction):
    Params = (TIME_PARAM_EVENT_EPOCH,)

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self, TIME_FUNCTION_TYPE_STEP, definition, self.Params
        )
        self._epoch = self._params[TIME_PARAM_EVENT_EPOCH]

    def refFunc(self, epoch):
        return 1.0 if epoch >= self._epoch else 0.0


class ExponentialTimeFunction(BaseTimeFunction):
    Params = (
        TIME_PARAM_EVENT_EPOCH,
        TIME_PARAM_TIME_CONSTANT,
    )

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_EXPONENTIAL,
            definition,
            self.Params,
        )
        self._epoch = self._params[TIME_PARAM_EVENT_EPOCH]
        self._decay = self._params[TIME_PARAM_TIME_CONSTANT]

    def refFunc(self, epoch):
        epoch -= self._epoch
        if epoch < 0.0:
            return 0.0
        return 1.0 - math.exp(-epoch / self._decay)


class LogarithmicTimeFunction(BaseTimeFunction):
    Params = (
        TIME_PARAM_EVENT_EPOCH,
        TIME_PARAM_TIME_CONSTANT,
    )

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_LOGARITHMIC,
            definition,
            self.Params,
        )
        self._epoch = self._params[TIME_PARAM_EVENT_EPOCH]
        self._decay = self._params[TIME_PARAM_TIME_CONSTANT]

    def refFunc(self, epoch):
        epoch -= self._epoch
        if epoch < 0.0:
            return 0.0
        return math.log(1.0 + epoch / self._decay)


class RampTimeFunction(BaseTimeFunction):
    Params = (
        TIME_PARAM_START_EPOCH,
        TIME_PARAM_END_EPOCH,
    )

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_RAMP,
            definition,
            self.Params,
        )
        self._epoch0 = self._params[TIME_PARAM_START_EPOCH]
        self._epoch1 = self._params[TIME_PARAM_END_EPOCH]
        self._epochDiff = self._epoch1 - self._epoch0

    def refFunc(self, epoch):
        if epoch < self._epoch0:
            return 0.0
        elif epoch >= self._epoch1:
            return 1.0
        else:
            return (epoch - self._epoch0) / self._epochDiff


class CyclicTimeFunction(BaseTimeFunction):
    Params = (
        TIME_PARAM_FUNCTION_REFERENCE_EPOCH,
        TIME_PARAM_FREQUENCY,
    )

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_CYCLIC,
            definition,
            self.Params,
        )
        self._refEpoch = self._params[TIME_PARAM_FUNCTION_REFERENCE_EPOCH]
        self._frequency = self.param[TIME_PARAM_FREQUENCY]

    def refFunc(self, epoch):
        return math.sin(self._frequency * (epoch - self._refEpoch) / (2.0 * math.pi))


class HyperbolicTangentTimeFunction(BaseTimeFunction):
    Params = (
        TIME_PARAM_EVENT_EPOCH,
        TIME_PARAM_TIME_CONSTANT,
    )

    def __init__(self, definition):
        BaseTimeFunction.__init__(
            self,
            TIME_FUNCTION_TYPE_HYPERBOLIC_TANGENT,
            definition,
            self.Params,
        )
        self._epoch = self._params[TIME_PARAM_EVENT_EPOCH]
        self._timeFactor = self._params[TIME_PARAM_TIME_CONSTANT]

    def refFunc(self, epoch):
        return math.tanh((epoch - self._epoch) / self._timeFactor)


class CompoundTimeFunction:
    def __init__(self, minEpoch=None, maxEpoch=None):
        self._baseFunctions = []
        self._minEpoch = minEpoch
        self._maxEpoch = maxEpoch
        self._cacheEpoch0 = None
        self._cacheValue0 = None
        self._cacheEpoch1 = None
        self._cacheValue1 = None

    def addFunction(self, function: BaseTimeFunction):
        self._baseFunctions.append(function)
        self._cacheEpoch0 = None
        self._cacheValue0 = None
        self._cacheEpoch1 = None
        self._cacheValue1 = None

    def _evaluate(self, epoch):
        if self._minEpoch is not None and epoch < self._minEpoch:
            return None
        if self._maxEpoch is not None and epoch > self._maxEpoch:
            return None
        return sum((f.valueAt(epoch) for f in self._baseFunctions))

    def valueAt(self, epoch):
        if self._cacheEpoch0 is None or epoch != self._cacheEpoch0:
            self._cacheEpoch0 = self._evaluate(epoch)
        return self._cacheEpoch0

    def valueChange(self, epoch, refepoch):
        if self._cacheEpoch1 is None or epoch != self._cacheEpoch1:
            self._cacheEpoch1 = self._evaluate(epoch)
        value1 = self._cacheEpoch1
        value0 = self.valueAt(refepoch)
        if value1 is None or value0 is None:
            return None
        else:
            return value1 - value0
