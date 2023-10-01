#!/bin/sh
rm -f ca_ntv2.ggxf ca_ntv2.cdl
python3 ../../../scripts/ggxf.py convert -v ca_ntv2.yaml -n write-cdl=header-clean ca_ntv2.ggxf
# ncdump ca_ntv2.ggxf > ca_ntv2.cdl
