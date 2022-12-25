FROM osgeo/gdal
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    python3-yaml python3-netcdf4  python3-numpy vim-tiny \
    && rm -rf /var/lib/apt/lists/*
COPY GGXF /usr/local/lib/ggxf/GGXF
COPY ggxf.py /usr/bin/ggxf
ENV PYTHONPATH /usr/local/lib/ggxf
ENV PS1="ggxf> "
ENV PS2="....> "
CMD ["ggxf"]

