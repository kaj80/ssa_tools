#!/bin/bash

make_opt="-j$(nproc)"

basedir=$1
status=0
for dir in "$basedir"/*; do
    if test -d "$dir"; then
        echo $dir
	cd $dir && ./autogen.sh && ./configure CFLAGS="-g -O0 -rdynamic"  && make $make_opt && sudo make $make_op install
	rc=$?
	if [[ $rc -ne 0 ]]; then
		echo "Failed to build $dir"
		let status=status+rc
	fi
    fi
done
exit $status
