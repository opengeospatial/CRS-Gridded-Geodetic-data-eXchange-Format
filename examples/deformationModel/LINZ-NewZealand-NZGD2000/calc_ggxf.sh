#!/bin/sh
python3 ../../../scripts/ggxf.py nzgd2000-20180701.ggxf -c test_points.csv -e 2015.0 --csv-decimal-places=4 --csv-summary nzgd2000-20180701-grids.csv
python3 ../../../scripts/ggxf.py nzgd2000-20180701.ggxf -y write-headers-only -o nzgd2000-headers.yaml
