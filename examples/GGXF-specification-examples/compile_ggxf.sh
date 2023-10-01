#!/bin/bash
for yaml in *.yaml; do
    ggxf="${yaml%.yaml}.ggxf"
    echo "=================================================================="
    echo "Loading ${yaml}"
    dummy="-y create-dummy-grid-data=y"
    if [[ $yaml != *"no-data.yaml" ]]; then dummy=''; fi
    echo python3 ../../scripts/ggxf.py convert -v $dummy -n write-cdl=header-clean "${yaml}" "${ggxf}"
    python3 ../../scripts/ggxf.py convert -v $dummy -n write-cdl=header-clean "${yaml}" "${ggxf}"
done