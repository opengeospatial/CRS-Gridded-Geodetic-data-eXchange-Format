#!/bin/bash
for yaml in *.yaml; do
    ggxf="${yaml%.yaml}.ggxf"
    echo "=================================================================="
    echo "Loading ${yaml}"
    dummy="-y create_dummy_grid_data"
    if [ $yaml = "GGXFspec-E2_grid.yaml" ]; then dummy=''; fi
    python3 ../../scripts/ggxf.py -v $dummy -n write_cdl_header=true "${yaml}" -o "${ggxf}"
done