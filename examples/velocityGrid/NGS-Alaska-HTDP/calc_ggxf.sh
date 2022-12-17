#!/bin/sh
python3 ../../../scripts/ggxf.py alaska_velocity.ggxf -g -c test_points.csv --csv-decimal-places=4 > calc_ggxf.log 2>&1
