#!/bin/sh
rm -f *.ggxf *.cdl
grid=SAGeoid2010_Dataset
python3 ../../../scripts/ggxf.py convert -n write-cdl=header -v ${grid}.yaml ${grid}.ggxf
