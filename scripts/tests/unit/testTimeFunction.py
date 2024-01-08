import os
import sys

testdir = os.path.dirname(__file__)
srcdir = "../.."
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest

from GGXF.TimeFunction import BaseTimeFunction, DateToEpoch


class TimeTest(unittest.TestCase):
    def _runtimetest(self, name, metadata, tests):
        function = BaseTimeFunction.Create(metadata)
        for epoch, expected in tests:
            testval = function.valueAt(epoch)
            self.assertAlmostEqual(
                testval,
                expected,
                msg=f"test {name} epoch {epoch} expected {expected} got {testval}",
            )

    def test_DateToEpoch(self):
        self.assertAlmostEqual(
            DateToEpoch("2003-01-02"), 2003.00273972, msg="Convert simple date"
        )
        self.assertAlmostEqual(
            DateToEpoch("1998-08-29"), 1998.6575342, msg="Convert simple date"
        )

        self.assertAlmostEqual(
            DateToEpoch("2003-01-01T12:00:00Z"),
            2003.00136986,
            msg="Convert datetime date",
        )

        self.assertAlmostEqual(
            DateToEpoch("1998-12-31T23:59:59"), 1999.0, msg="Convert datetime date"
        )

    def test_LinearTimeFunction(self):
        metadata = {
            "functionType": "linear",
            "functionReferenceEpoch": 2003.0,
        }
        self._runtimetest(
            "basic linear function",
            metadata,
            ((2003.0, 0.0), (2013.0, 10.0), (1999.5, -3.5)),
        )
        metadata = {
            "functionType": "linear",
            "functionReferenceDate": "2003-01-01",
        }
        self._runtimetest(
            "basic linear function using date",
            metadata,
            ((2003.0, 0.0), (2013.0, 10.0), (1999.5, -3.5)),
        )
        metadata = {
            "functionType": "linear",
            "functionReferenceEpoch": "2003.0",
            "startEpoch": "2001.5",
        }
        self._runtimetest(
            "linear function with start epoch",
            metadata,
            ((2003.0, 0.0), (2013.0, 10.0), (1999.5, -1.5)),
        )
        metadata = {
            "functionType": "linear",
            "functionReferenceEpoch": "2003.0",
            "startEpoch": "2001.5",
            "endEpoch": "2005.5",
        }
        self._runtimetest(
            "linear function with start epoch",
            metadata,
            ((2003.0, 0.0), (2013.0, 2.5), (1999.5, -1.5)),
        )


if __name__ == "__main__":
    unittest.main()
