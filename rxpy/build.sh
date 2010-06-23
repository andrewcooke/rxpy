#!/bin/bash

# IMPORTANT - update version in setup.py

# this generates a new release, but does not register anything with pypi
# or upload files to google code.

# python setup.py sdist --formats=gztar,zip register upload

 
RELEASE=`egrep "version=" setup.py | sed -e "s/.*'\(.*\)'.*/\\1/"`
VERSION=`echo $RELEASE | sed -e "s/.*?\([0-9]\.[0-9]\).*/\\1/"`

rm -fr dist MANIFEST*

python setup.py sdist --formats=gztar,zip

#./build-doc.sh

rm -fr "RXPY-$RELEASE"
mkdir "RXPY-$RELEASE"
cp -r doc "RXPY-$RELEASE"
tar cvfz "dist/RXPY-$RELEASE-doc.tar.gz" "RXPY-$RELEASE"
zip -r "dist/RXPY-$RELEASE-doc.zip" "RXPY-$RELEASE" -x \*.tgz
rm -fr "RXPY-$RELEASE"

#./push-docs.sh
