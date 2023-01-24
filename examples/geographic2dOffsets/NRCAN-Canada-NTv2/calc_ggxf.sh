#!/bin/sh
python3 ../../../scripts/ggxf.py calculate -v ca_ntv2.ggxf test_points.csv test_points-out.csv --csv-decimal-places 6 
python3 ../../../scripts/ggxf.py describe -v ca_ntv2.ggxf --csv-grid-summary ca_ntv2_grids.csv > ca_ntv2_ggxf.txt
