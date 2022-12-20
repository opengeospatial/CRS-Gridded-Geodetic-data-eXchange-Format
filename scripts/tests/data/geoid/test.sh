#!/bin/sh

ggxf=../../../ggxf.py
outdir="out"
chkdir="check"

rm -f $outdir/test*
"$ggxf" test-inline.yaml -y write-csv-grids=no -o $outdir/test-inline-out.yaml
"$ggxf" test-inline.yaml -o $outdir/test-inline-csv-out.yaml
"$ggxf" test-inline.yaml -n write-cdl=yes -o $outdir/test-inline-out.ggxf
"$ggxf" test-ggxf-csv.yaml -y write-csv-grids=no -o $outdir/test-ggxf-csv-out.yaml
"$ggxf" test-netcdf.ggxf -y write-csv-grids=no -o $outdir/test-netcdf-out.yaml
"$ggxf" test-gdal.yaml  -y write-csv-grids=no -o $outdir/test-gdal-out.yaml
"$ggxf" test-inline.yaml -c test-points.csv --output-csv-file $outdir/test-points-out.csv

status=0
for file in $(ls check); do
    outfile="$outdir/${file}"
    chkfile="$chkdir/${file}"
    if ! [ -f "$outfile" ]; then
        echo "Output file $file not generated"
        status=1
    elif ! diff -q "${outfile}" "${chkfile}" ; then
        echo "Output file $file doesn't match check"
        status=1
    fi
done

if [ "$status" = "0" ]; then
   echo "All geoid checks passed"
fi
exit $status