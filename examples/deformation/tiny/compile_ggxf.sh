#!/bin/sh
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 deformation.yaml deformation_dot0.nc
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m json deformation.yaml deformation_json.nc
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 defnested.yaml defnested.nc