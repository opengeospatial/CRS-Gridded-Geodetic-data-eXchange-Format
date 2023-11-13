#!/bin/sh
python3 ../../../scripts/ggxf.py convert -v EuVem2022_ETRF2000.yaml -n write-cdl=header-clean EuVem2022_ETRF2000.ggxf 
python3 ../../../scripts/ggxf.py convert -v EuVem2022_ETRF2014.yaml -n write-cdl=header-clean EuVem2022_ETRF2014.ggxf 
python3 ../../../scripts/ggxf.py check -v EuVem2022_ETRF2014.ggxf
