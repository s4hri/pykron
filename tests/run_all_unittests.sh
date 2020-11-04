#!/usr/bin/env bash

# Unit tests
#

cd unit
python3 -m unittest discover . -v
cd ..