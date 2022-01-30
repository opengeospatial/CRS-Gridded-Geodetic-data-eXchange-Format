#!/bin/sh
echo "Runtime: `date "+%Y-%m-%d %H:%M:%S"`" > build.log
if [ "$1" = "compile" -o "$1" = "" ]; then
    for f in `find . -name compile_ggxf.sh -executable`; do (
        echo '=============================================='
        echo "Executing $f"
        cd `dirname $f`
        ./`basename $f`
    ) >> build.log 2>&1; done
fi

if [ "$1" = "calc" -o "$1" = "" ]; then
    for f in `find . -name '*-out.csv.chk'`; do
        cf=`dirname $f`/`basename $f .chk`
        rm -f $cf
    done
    for f in `find . -name calc_ggxf.sh -executable`; do (
        echo '=============================================='
        echo "Executing $f"
        cd `dirname $f`
        ./`basename $f`
    ) >> build.log 2>&1; done
    echo "Testing calculation output files"
    for f in `find . -name '*-out.csv.chk'`; do
        cf=`dirname $f`/`basename $f .chk`
        echo "Testing $cf"
        if `diff $cf $f`; then
            echo "Passed"
        fi
    done
fi

grep ERROR build.log
grep WARNING build.log | sort | uniq
