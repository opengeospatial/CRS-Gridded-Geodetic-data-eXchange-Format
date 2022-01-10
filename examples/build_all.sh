#!/bin/sh
if [ "$1" = "compile" -o "$1" = "" ]; then
    for f in `find . -name compile_ggxf.sh -executable`; do (
        echo '=============================================='
        echo "Executing $f"
        cd `dirname $f`
        ./`basename $f`
    ) done
fi

if [ "$1" = "calc" -o "$1" = "" ]; then
    for f in `find . -name calc_ggxf.sh -executable`; do (
        echo '=============================================='
        echo "Executing $f"
        cd `dirname $f`
        ./`basename $f`
    ) done
fi
