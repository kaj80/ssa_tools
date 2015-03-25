#!/bin/bash   
basedir=$1
for dir in "$basedir"/*; do
    if test -d "$dir"; then
        echo $dir
	cd $dir && ./autogen.sh && ./configure CFLAGS="-g -O0 -rdynamic" --prefix="/usr" && make -j && sudo make install
        
    fi
done
