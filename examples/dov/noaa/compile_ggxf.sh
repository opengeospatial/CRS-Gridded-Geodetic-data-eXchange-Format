#!/bin/sh
ggxf PRVI_DOV18.yaml -n write_cdl_header=true -o PRVI_DOV18.ggxf
ncdump -h PRVI_DOV18.ggxf > PRVI_DOV18.cdl