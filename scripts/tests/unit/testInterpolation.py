import sys, os

#!! NOTE These tests are not complete.  Not testing points off the grid.  Also because test grids exactly match
# interpolation method (eg cubic for bicubic interpolation) this doesn't confirm that the correct grid cells are
# being used in the interpolation.

testdir = os.path.dirname(__file__)
srcdir = "../.."
sys.path.insert(0, testdir)
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest
import numpy as np
from DummyGGXF import dummyGroup
from GGXF import GGXF
from GGXF.GGXF import GridInterpolator, Grid


defaultAffine = [172.0, 0.3, 0.0, 41.5, 0.0, 0.4]


def createGrid(size, generators=None, data=None, affine=defaultAffine):
    if generators:
        nparam = len(generators)
        size = [size[0], size[1], nparam]
        data = np.zeros(size)
        for i in range(size[0]):
            for j in range(size[1]):
                for k in range(size[2]):
                    data[i, j, k] = generators[k](i, j)
    else:
        data = np.array(data)
        if data.size % (size[0] * size[1]) == 0:
            size = [size[0], size[1], data.size // (size[0] * size[1])]
            data = data.reshape(size)
    metadata = {
        GGXF.GRID_ATTR_I_NODE_COUNT: size[0],
        GGXF.GRID_ATTR_J_NODE_COUNT: size[1],
        GGXF.GRID_ATTR_AFFINE_COEFFS: affine,
    }
    grid = Grid(dummyGroup(nparam=size[2]), "Test grid", metadata)
    grid.setData(data)
    # print(size)
    # print(data)
    return grid


def convertTestPoints(testpoints, affine=defaultAffine):
    tfm = np.array(affine).reshape(2, 3)
    testxy = []
    for xy in testpoints:
        xya = np.array([1.0, xy[0], xy[1]])
        testxy.append(tfm.dot(xya).tolist())
    return testxy


class BilinearInterpolationTest(unittest.TestCase):
    def setUp(self):
        gen1 = lambda x, y: 0.3 - 0.5 * x + 0.1 * y
        gen2 = lambda x, y: -1.5 - 0.05 * x + 1.2 * y
        self.testgrid1 = createGrid((3, 5), [gen1])
        self.checkfunc1 = lambda point: [gen1(point[0], point[1])]
        self.testgrid2 = createGrid((3, 5), [gen1, gen2])
        self.checkfunc2 = lambda point: [
            gen1(point[0], point[1]),
            gen2(point[0], point[1]),
        ]
        self.testpoints = [
            [1.2, 2.8],
            [0.0, 0.0],
            [1.0, 2.0],
            [0.7, 3.8],
            [1.9, 3.6],
            [1.9, 0.1],
        ]
        self.badpoints = [
            [-0.1, 1.5],
            [2.1, 1.5],
            [1.5, -0.1],
            [1.5, 4.1],
            [-0.1, -0.1],
        ]

    def test_Bilinear1(self):
        testxy = convertTestPoints(self.testpoints)
        for xy, point in zip(testxy, self.testpoints):
            result = GridInterpolator.bilinear(self.testgrid1, xy)
            check = self.checkfunc1(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Bilinear interpolation at {point}"
            )

    def test_Bilinear2(self):
        testxy = convertTestPoints(self.testpoints)
        for xy, point in zip(testxy, self.testpoints):
            result = GridInterpolator.bilinear(self.testgrid2, xy)
            check = self.checkfunc2(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Bilinear interpolation at {point}"
            )


class BiquadraticInterpolationTest(unittest.TestCase):
    def setUp(self):
        gen1 = lambda x, y: 0.3 - 0.5 * x + 0.1 * y + 0.05 * x * x - 0.02 * x * y
        gen2 = lambda x, y: -1.5 - 0.05 * x + 1.2 * y + 0.3 * x * y - 0.25 * y * y
        self.testgrid1 = createGrid((3, 5), [gen1])
        self.checkfunc1 = lambda point: [gen1(point[0], point[1])]
        self.testgrid2 = createGrid((3, 5), [gen1, gen2])
        self.checkfunc2 = lambda point: [
            gen1(point[0], point[1]),
            gen2(point[0], point[1]),
        ]
        self.testpoints = [
            [1.2, 2.8],
            [0.0, 0.0],
            [1.0, 2.0],
            [0.7, 3.8],
            [1.9, 3.6],
            [1.9, 0.1],
        ]
        self.badpoints = [
            [-0.1, 1.5],
            [2.1, 1.5],
            [1.5, -0.1],
            [1.5, 4.1],
            [-0.1, -0.1],
        ]
        gen3 = lambda x, y: max(-1, min(1, 2 * (x - 1.5)))
        self.testgrid3 = createGrid((4, 4), [gen3])
        self.checkfunc3 = lambda point: [
            (point[0] - 0.5) ** 2 - 1.25
            if point[0] < 1.5
            else 1.25 - (point[0] - 2.5) ** 2
        ]
        self.testpoints3 = [
            [0.5, 1.0],
            [1.0, 1.0],
            [1.45, 1.0],
            [1.55, 1.0],
            [2.0, 1.0],
            [2.9, 1.0],
        ]
        gen4 = lambda x, y: max(-1, min(1, 2 * (y - 1.5)))
        self.testgrid4 = createGrid((4, 4), [gen4])
        self.checkfunc4 = lambda point: self.checkfunc3([point[1], point[0]])
        self.testpoints4 = [
            [1.0, 0.5],
            [1.0, 1.0],
            [1.0, 1.45],
            [1.0, 1.55],
            [1.0, 2.0],
            [1.0, 2.9],
        ]

    def test_Biquadratic1(self):
        testxy = convertTestPoints(self.testpoints)
        for xy, point in zip(testxy, self.testpoints):
            result = GridInterpolator.biquadratic(self.testgrid1, xy)
            check = self.checkfunc1(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Biquadratic interpolation at {point}"
            )

    def test_Biquadratic2(self):
        testxy = convertTestPoints(self.testpoints)
        for xy, point in zip(testxy, self.testpoints):
            result = GridInterpolator.biquadratic(self.testgrid2, xy)
            check = self.checkfunc2(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Biquadratic interpolation at {point}"
            )

    def test_Biquadratic3(self):
        testxy = convertTestPoints(self.testpoints3)
        for xy, point in zip(testxy, self.testpoints3):
            result = GridInterpolator.biquadratic(self.testgrid3, xy)
            check = self.checkfunc3(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Biquadratic interpolation at {point}"
            )
        testxy = convertTestPoints(self.testpoints4)
        for xy, point in zip(testxy, self.testpoints4):
            result = GridInterpolator.biquadratic(self.testgrid4, xy)
            check = self.checkfunc4(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Biquadratic interpolation at {point}"
            )

    def test_Biquadratic4(self):
        # Test based on example in NOAA Technical Memorandum NOS NGS 84 section 2
        # data = [[100.0, 107.0, 124.0], [92.0, 99.0, 94.0], [88.0, 106.0, 93.0]]
        data = [[100.0, 92.0, 88.0], [107.0, 99.0, 106.0], [124.0, 94.0, 93.0]]
        affine = [50.0, 25.0, 0.0, 10.0, 0.0, 10.0]
        xy = [87.0, 17.0]
        grid = createGrid((3, 3), data=data, affine=affine)
        result = GridInterpolator.biquadratic(grid, xy)
        self.assertAlmostEqual(
            result[0],
            100.601,
            places=3,
            msg=f"Biquadratic interpolation of NOAA example",
        )


class BicubicInterpolationTest(unittest.TestCase):
    def setUp(self):
        gen1 = lambda x, y: 0.3 - 0.5 * x + 0.1 * y + 0.2 * x * y * y - 0.05 * x * x * x
        gen2 = (
            lambda x, y: -1.5
            - 0.05 * x
            + 1.2 * y
            - 1.2 * x * y
            + 0.3 * y * y * x
            + 0.02 * y * y * y
        )
        self.testgrid1 = createGrid((4, 5), [gen1])
        self.checkfunc1 = lambda point: [gen1(point[0], point[1])]
        self.testgrid2 = createGrid((4, 5), [gen1, gen2])
        self.checkfunc2 = lambda point: [
            gen1(point[0], point[1]),
            gen2(point[0], point[1]),
        ]
        self.testpoints = [
            [1.2, 2.8],
            [0.0, 0.0],
            [1.0, 2.0],
            [0.7, 3.8],
            [2.9, 3.6],
            [2.9, 0.1],
        ]
        self.badpoints = [
            [-0.1, 1.5],
            [3.1, 1.5],
            [1.5, -0.1],
            [1.5, 4.1],
            [-0.1, -0.1],
        ]

    def test_Bicubic1(self):
        testxy = convertTestPoints(self.testpoints)
        for xy, point in zip(testxy, self.testpoints):
            result = GridInterpolator.bicubic(self.testgrid1, xy)
            check = self.checkfunc1(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Bicubic interpolation at {point}"
            )

    def test_Bicubic2(self):
        testxy = convertTestPoints(self.testpoints)
        for xy, point in zip(testxy, self.testpoints):
            result = GridInterpolator.bicubic(self.testgrid2, xy)
            check = self.checkfunc2(point)
            self.assertAlmostEqual(
                result[0], check[0], msg=f"Bicubic interpolation at {point}"
            )


if __name__ == "__main__":
    unittest.main()
