#!/bin/bash
for yaml in *.yaml; do
    ggxf="${yaml%.yaml}.ggxf"
    echo "=================================================================="
    echo "Loading ${yaml}"
    python3 ../../scripts/ggxf.py -v -y create_dummy_grid_data -n write_cdl_header=true "${yaml}" -o "${ggxf}"
done