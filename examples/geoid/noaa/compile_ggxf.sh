#!/bin/sh
rm -f *.ggxf *.cdl
python3 ../../../scripts/GGXF.py -v PRGEOID18-header-block-then-grid-block.yaml -o PRGEOID18a.ggxf --dump-grid all prgeoid18a-grid.csv
ncdump PRGEOID18a.ggxf > PRGEOID18a.cdl
python3 ../../../scripts/GGXF.py -v PRGEOID18-header-plus-grid-block.yaml -o PRGEOID18b.ggxf --dump-grid all prgeoid18b-grid.csv
ncdump PRGEOID18b.ggxf > PRGEOID18b.cdl
python3 ../../../scripts/GGXF.py -v PRGEOID18-with-external-grid-ref.yaml -o PRGEOID18c.ggxf -y check_datasource_affine_coeffs=false  --dump-grid all prgeoid18c-grid.csv
ncdump PRGEOID18c.ggxf > PRGEOID18c.cdl
python3 ../../../scripts/GGXF.py -v VIGEOID18-header-block-then-grid-block.yaml -o VIGEOID18a.ggxf
ncdump VIGEOID18a.ggxf > VIGEOID18a.cdl
python3 ../../../scripts/GGXF.py -v VIGEOID18-header-plus-grid-block.yaml -o VIGEOID18b.ggxf
ncdump VIGEOID18b.ggxf > VIGEOID18b.cdl
#python3 ../../../scripts/GGXF.py -v VIGEOID18-with-external-grid-ref.yaml VIGEOID18c.ggxf
#ncdump  VIGEOID18c.ggxf > VIGEOID18c.cdl
