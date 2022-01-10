#!/bin/sh
rm -f ca_ntv2.gxb ca_ntv2.cdl
python3 ../../../scripts/GGXF.py -v ca_ntv2.yaml -n write_cdl=true -o ca_ntv2.gxb
# ncdump ca_ntv2.gxb > ca_ntv2.cdl
