#!/bin/bash   
basedir=$1
status=0
for dir in "$basedir"/*; do
    if test -d "$dir"; then
        echo $dir
	cd $dir && ./autogen.sh && ./configure CFLAGS="-g -O0 -rdynamic"  && make -j && sudo make install
	rc=$?
	if [[ $rc -ne 0 ]]; then
		echo "Failed to build $dir"
		let status=status+rc
	fi
    fi
done
exit $status
