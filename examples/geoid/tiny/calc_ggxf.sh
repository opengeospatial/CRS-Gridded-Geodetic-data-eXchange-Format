#!/bin/sh
python3 ../../../scripts/ggxf.py test_geoid.ggxf --list-grids --dump-grid 0:0 test.grid.csv -c test_points.csv -o test-out.yaml
