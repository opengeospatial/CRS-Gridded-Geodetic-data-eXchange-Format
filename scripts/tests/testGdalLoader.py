import sys, os

testdir = os.path.dirname(__file__)
srcdir = ".."
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest
import numpy as np
from GGXF.GridLoader import GDAL


class CsvLoaderTest(unittest.TestCase):
    def testCsvLoader(self):
        tiffile = os.path.join(testdir, "data", "test.tif")
        csvsource = {
            "gdalSource": tiffile,
        }
        (size, affine, data) = GDAL.LoadGrid(csvsource, None)

        self.assertEqual(size, (43, 40), f"Grid size - expected (43,40) but got {size}")
        affineExpected = [-38.625, 0.0, -0.125, 171.1, 0.15, 0.0]
        diff = max(np.abs(np.array(affine) - np.array(affineExpected)))
        self.assertTrue(
            diff < 0.000001,
            f"Affine transformation: expected {affineExpected} but got {affine}",
        )
        shape = tuple((int(n) for n in data.shape))
        self.assertEqual(
            shape, (40, 43, 2), f"Grid dimensions: expected (40,43,2) but got {shape}"
        )


if __name__ == "__main__":
    unittest.main()
