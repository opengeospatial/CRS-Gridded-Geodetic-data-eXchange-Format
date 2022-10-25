#!/bin/sh
rm -f *.ggxf *.cdl
python3 ../../../scripts/ggxf.py -n write_cdl_header=true -v PRGEOID18.yaml -o PRGEOID18.ggxf -n write_cdl_header=true 
python3 ../../../scripts/ggxf.py -n write_cdl_header=true -v VIGEOID18.yaml -o VIGEOID18.ggxf -n write_cdl_header=true 
