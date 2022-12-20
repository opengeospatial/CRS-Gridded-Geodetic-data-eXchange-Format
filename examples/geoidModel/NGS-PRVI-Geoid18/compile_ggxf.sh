#!/bin/sh
rm -f *.ggxf *.cdl
python3 ../../../scripts/ggxf.py -n write-cdl-header=true -v PRGEOID18.yaml -o PRGEOID18.ggxf -n write-cdl-header=true 
python3 ../../../scripts/ggxf.py -n write-cdl-header=true -v VIGEOID18.yaml -o VIGEOID18.ggxf -n write-cdl-header=true 
