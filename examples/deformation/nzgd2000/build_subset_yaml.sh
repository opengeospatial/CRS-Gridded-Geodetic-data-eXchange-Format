#!/bin/sh
python3 ../../../scripts/deformation_model_to_ggxf_yaml.py  -m nzgd2000_meta.yaml -d 2 -w 2 --discard-temporal-extent -g nz_linz_nzgd2000-ds20090715-grid011 -g nz_linz_nzgd2000-ndm-grid02 nzdm/nz_linz_nzgd2000-20180701.json nzgd2000-20180701-subset.yaml
