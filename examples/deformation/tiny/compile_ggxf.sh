#!/bin/sh
rm -f *.ggxf *.cdl
echo "Dot 1 metadata format"
python3 ../../../scripts/GGXF.py -v -n write_cdl=true deformation.yaml -o deformation.ggxf
echo "Using compound types"
python3 ../../../scripts/GGXF.py -v  -n use_compound_types=true -n write_cdl=true deformation.yaml -o deformation_compound.ggxf
echo "Using gridData section in YAML file"
python3 ../../../scripts/GGXF.py -v def_griddata.yaml -n write_cdl=true -o def_griddata.ggxf