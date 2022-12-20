#!/bin/bash
for yaml in *.yaml; do
    ggxf="${yaml%.yaml}.ggxf"
    echo "=================================================================="
    echo "Loading ${yaml}"
    dummy="-y create-dummy-grid-data=y"
    if [[ $yaml != *"no-data.yaml" ]]; then dummy=''; fi
    echo python3 ../../scripts/ggxf.py -v $dummy -n write-cdl-header=true "${yaml}" -o "${ggxf}"
    python3 ../../scripts/ggxf.py -v $dummy -n write-cdl-header=true "${yaml}" -o "${ggxf}"
done