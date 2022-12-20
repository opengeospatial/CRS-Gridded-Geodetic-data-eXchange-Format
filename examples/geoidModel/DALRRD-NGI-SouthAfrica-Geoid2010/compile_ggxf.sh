#!/bin/sh
rm -f *.ggxf *.cdl
grid=SAGeoid2010_Dataset
python3 ../../../scripts/ggxf.py -n write-cdl-header=true -v ${grid}.yaml -o ${grid}.ggxf
