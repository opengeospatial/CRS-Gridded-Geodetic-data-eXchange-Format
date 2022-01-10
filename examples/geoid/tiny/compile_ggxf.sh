#!/bin/sh
rm -f test_geoid.gxb test_geoid.cdl
python3 ../../../scripts/GGXF.py -v -n write_cdl=true test_geoid.yaml -o test_geoid.gxb