NZGD2000 deformation model
==========================

The NZGD2000 deformation model GGXF dataset is compiled from the JSON/GeoTIFF implementation
in the nzdm directory.  The build_yaml.sh script compiles the yaml file using the script
in scripts/deformation_model_to_ggxf_yaml.py.  In addition to the deformation model in the
nzdm directory it uses additional metadata from the nzgd2000_meta.yaml file.

The script build_subset_yaml.sh can be used to build a relatively small subset of the full
model by cutting most of the grids out of the model.  This is for demonstration/testing only,
the subset it generates does not represent the true value of the NZGD2000 deformation model.
