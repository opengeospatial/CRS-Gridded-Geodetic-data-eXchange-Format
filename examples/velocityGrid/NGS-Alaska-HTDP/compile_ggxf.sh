#!/bin/sh
python3 ../../../scripts/ggxf.py -v -y grid-directory=grids alaska_velocity.yaml -n write-cdl-header=true -o  alaska_velocity.ggxf --csv-summary=alaska-grids.csv
