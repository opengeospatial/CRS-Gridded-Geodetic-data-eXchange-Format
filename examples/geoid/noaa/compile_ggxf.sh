#!/bin/sh
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 PRGEOID18-header-block-then-grid-block.yaml PRGEOID18a.nc
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 PRGEOID18-header-plus-grid-block.yaml PRGEOID18b.nc
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 PRGEOID18-with-external-grid-ref.yaml PRGEOID18c.nc
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 VIGEOID18-header-block-then-grid-block.yaml VIGEOID18a.nc
python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 VIGEOID18-header-plus-grid-block.yaml VIGEOID18b.nc
#python3 ../../../scripts/ggxf_yaml_to_netcdf4.py -v -d -m dot0 VIGEOID18-with-external-grid-ref.yaml VIGEOID18c.nc
