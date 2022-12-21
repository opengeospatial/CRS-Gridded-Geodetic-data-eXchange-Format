#!/bin/sh
rm -f *.ggxf *.cdl
python3 ../../../scripts/ggxf.py convert -n write-cdl=header -v PRGEOID18.yaml PRGEOID18.ggxf -n write-cdl=header 
python3 ../../../scripts/ggxf.py convert -n write-cdl=header -v VIGEOID18.yaml VIGEOID18.ggxf -n write-cdl=header 
