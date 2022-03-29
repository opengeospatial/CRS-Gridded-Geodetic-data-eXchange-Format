#!/bin/sh
python3 ../../../scripts/GGXF.py nzgd2000-20180701.ggxf -g -c test_points.csv -e 2015.0 --csv-decimal-places=4 --csv-summary nzgd2000-20180701-grids.csv > calc_ggxf.log 2>&1
python3 ../../../scripts/GGXF.py nzgd2000-20180701.ggxf -y write_headers_only -y used_nested_grids=false-o nzgd2000-headers.yaml >> calc_ggxf.log 2>&1
