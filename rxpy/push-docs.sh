#!/bin/bash

pushd ~/projects/personal/www/rxpy
svn update
svn remove --force *
svn commit -m "rxpy"
popd
rsync -rv --exclude=".svn" --delete doc/ ~/projects/personal/www/rxpy
pushd ~/projects/personal/www/rxpy
svn add *
svn commit -m "rxpy"
popd

