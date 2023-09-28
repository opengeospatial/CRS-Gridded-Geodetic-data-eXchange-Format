#!/bin/bash

prefix="$1"
testdir="$(dirname "$(realpath "$0")")"
cd "$testdir"

ggxf="$(realpath ../../ggxf.py)"
srcdir="../data"
outdir="out"
chkdir="check"
status=0

for testfile in "$prefix"*.test; do (
    testname=$(basename "$testfile" .test)
    echo "Running test $testname"
    rundir="$outdir/$testname"
    rm -rf "$rundir"
    mkdir -p "$rundir"
    # Load test configuration
    files=
    command=
    source "$testfile"
    # Copy required files to the run directory
    for input_file in ${files}; do
        cp "$srcdir/$input_file" "$rundir"
    done

    # Run the script and clean up in the run directory
    (
        # Run the script
        cd "$rundir"
        python3 "$ggxf" $command > "$testname.log"
        # Remove the input files 
        for input in $files; do
            rm -f $(basename "$input")
        done
        # Remove binary ggxf files - will use CDL for confirmation of content
        rm -f *.ggxf
        # Remove potentially incompatible NetCDF generated attributes from cdl
        for f in *.cdl; do
            if [ "$f" != "*.cdl" ]; then
                sed -i '/:_/ d' $f
            fi
        done
    )

    # Check the output files match the check

    if [ ! -d  "$chkdir/$testname" ]; then
        echo " - no checks available for $testname"
    elif diff -qr "$chkdir/$testname" "$rundir"; then
        echo " - test passed"
    else
        echo " - **** test failed"
        status=1
    fi
)
done
exit $status