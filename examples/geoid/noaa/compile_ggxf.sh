#!/bin/sh
rm -f *.ggxf *.cdl
python3 ../../../scripts/ggxf.py -n write_cdl_header=true -v PRGEOID18.yaml -o PRGEOID18.ggxf -y check_datasource_affine_coeffs=false -n write_cdl_header=true 
