#!/bin/bash   
basedir=$1
for dir in "$basedir"/*; do
    if test -d "$dir"; then
        echo $dir
        cd $dir && ./autogen.sh && ./configure --prefix="/usr" && make -j && sudo make install
        
    fi
done
