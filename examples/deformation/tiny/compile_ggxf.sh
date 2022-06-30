#!/bin/sh
rm -f *.ggxf *.cdl
echo "Dot 0 metadata format"
python3 ../../../scripts/GGXF.py -v -n metadata_style=dot0 -n write_cdl=true deformation.yaml -o deformation_dot0.ggxf
echo "Dot 1 metadata format"
python3 ../../../scripts/GGXF.py -v -n metadata_style=dot1 -n write_cdl=true deformation.yaml -o deformation_dot1.ggxf
echo "JSON metadata format"
python3 ../../../scripts/GGXF.py -v -n metadata_style=json deformation.yaml -n write_cdl=true -o deformation_json.ggxf
echo "Using gridData section in YAML file"
python3 ../../../scripts/GGXF.py -v -n metadata_style=dot0 def_griddata.yaml -n write_cdl=true -o def_griddata_dot0.ggxf