#!/bin/sh
python3 ../../../scripts/ggxf.py -v -y grid_directory=grids alaska_velocity.yaml -n write_cdl_header=true -o  alaska_velocity.ggxf --csv-summary=alaska-grids.csv
