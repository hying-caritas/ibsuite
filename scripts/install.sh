#!/bin/sh

set -e

cwd=$(pwd)

cp -r root/* /

cd ibpy
python setup.py install
