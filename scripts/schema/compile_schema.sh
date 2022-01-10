#!/bin/sh

rm -f Constants.py GGXF_Types.py
if python3 schema_yaml_to_py.py; then
  if which black >/dev/null 2>&1; then
    if ! black -q Constants.py GGXF_Types.py; then
      exit
    fi
  fi
  mv Constants.py ../GGXF/
  mv GGXF_Types.py ../GGXF/
fi
