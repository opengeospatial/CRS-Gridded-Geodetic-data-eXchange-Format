#!/bin/sh
rm -f *.ggxf *.cdl
# python3 ../../../scripts/ggxf.py -v PRGEOID18-header-block-then-grid-block.yaml -o PRGEOID18a.ggxf --dump-grid all prgeoid18a-grid.csv
# python3 ../../../scripts/ggxf.py -v PRGEOID18-header-plus-grid-block.yaml -o PRGEOID18b.ggxf --dump-grid all prgeoid18b-grid.csv
python3 ../../../scripts/ggxf.py -n write_cdl_header=true -v PRGEOID18-with-external-grid-ref.yaml -o PRGEOID18.ggxf -y check_datasource_affine_coeffs=false -n write_cdl_header=true 
python3 ../../../scripts/ggxf.py -v VIGEOID18-header-block-then-grid-block.yaml -o VIGEOID18.ggxf -n write_cdl_header=true
# python3 ../../../scripts/ggxf.py -v VIGEOID18-header-plus-grid-block.yaml -o VIGEOID18b.ggxf
# python3 ../../../scripts/ggxf.py -v VIGEOID18-with-external-grid-ref.yaml -n write_cdl_header=true -o VIGEOID18.ggxf
