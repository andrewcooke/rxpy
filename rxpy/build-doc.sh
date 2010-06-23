#!/bin/bash

RELEASE=`egrep "version=" setup.py | sed -e "s/.*'\(.*\)'.*/\\1/"`
VERSION=`echo $RELEASE | sed -e "s/.*?\([0-9]\.[0-9]\).*/\\1/"`

sed -i -e "s/release = .*/release = '$RELEASE'/" doc-src/manual/conf.py
sed -i -e "s/version = .*/version = '$VERSION'/" doc-src/manual/conf.py

sed -i -e "s/__version__ = .*/__version__ = '$RELEASE'/" src/rxpy/__init__.py

rm -fr doc

#pushd doc-src/manual
#./index.sh
#popd

sphinx-build -b html doc-src/manual doc

# parse-only necessary or we lose all decorated functions
epydoc -v -o doc/api --parse-only --html --graph=all --docformat=restructuredtext -v --exclude="_experiment" --exclude="_performance" --exclude="_example" --debug src/*

cp doc-src/index.html doc
cp doc-src/index.css doc
cp src/rxpy/parser/_example/example-graph.png doc
