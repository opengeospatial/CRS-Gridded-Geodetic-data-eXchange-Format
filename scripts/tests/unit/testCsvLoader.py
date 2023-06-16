import os
import sys

testdir = os.path.dirname(os.path.dirname(__file__))
srcdir = ".."
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest

import numpy as np

from GGXF.GridLoader import CSV


class CsvLoaderTest(unittest.TestCase):
    def testCsvLoader(self):
        csvfile = os.path.join(testdir, "data", "test.csv")
        csvsource = {
            "gridFilename": csvfile,
            "interpolationCoordFields": ["X", "Y"],
            "parameterFields": ["displacementEast", "displacementNorth"],
        }
        (data, size, affine) = CSV.LoadGrid({}, csvsource, None)
        shapeExpected = (40, 43)
        self.assertEqual(
            size,
            shapeExpected,
            f"Grid size - expected {shapeExpected} but got {size}",
        )
        affineExpected = [-38.625, -0.125, 0.0, 171.1, 0.0, 0.15]
        diff = max(np.abs(np.array(affine) - np.array(affineExpected)))
        self.assertTrue(
            diff < 0.000001,
            f"Affine transformation: expected {affineExpected} but got {affine}",
        )
        shape = tuple((int(n) for n in data.shape))
        shapeExpected = (40, 43)
        self.assertEqual(
            size,
            shapeExpected,
            f"Grid size - expected {shapeExpected} but got {size}",
        )


if __name__ == "__main__":
    unittest.main()
