#!/bin/sh
rm -f *.gxb *.cdl
python3 ../../../scripts/GGXF.py -v PRGEOID18-header-block-then-grid-block.yaml -o PRGEOID18a.gxb --dump-grid all prgeoid18a-grid.csv
ncdump PRGEOID18a.gxb > PRGEOID18a.cdl
python3 ../../../scripts/GGXF.py -v PRGEOID18-header-plus-grid-block.yaml -o PRGEOID18b.gxb --dump-grid all prgeoid18b-grid.csv
ncdump PRGEOID18b.gxb > PRGEOID18b.cdl
python3 ../../../scripts/GGXF.py -v PRGEOID18-with-external-grid-ref.yaml -o PRGEOID18c.gxb -y check_datasource_affine_coeffs=false  --dump-grid all prgeoid18c-grid.csv
ncdump PRGEOID18c.gxb > PRGEOID18c.cdl
python3 ../../../scripts/GGXF.py -v VIGEOID18-header-block-then-grid-block.yaml -o VIGEOID18a.gxb
ncdump VIGEOID18a.gxb > VIGEOID18a.cdl
python3 ../../../scripts/GGXF.py -v VIGEOID18-header-plus-grid-block.yaml -o VIGEOID18b.gxb
ncdump VIGEOID18b.gxb > VIGEOID18b.cdl
#python3 ../../../scripts/GGXF.py -v VIGEOID18-with-external-grid-ref.yaml VIGEOID18c.gxb
#ncdump  VIGEOID18c.gxb > VIGEOID18c.cdl
