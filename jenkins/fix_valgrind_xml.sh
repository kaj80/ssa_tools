#!/bin/bash


for f in $@; do
	tail -2 $f | grep -q "</valgrindoutput>" || echo "</valgrindoutput>" >> $f
done

for f in $@; do
	start_num=`cat $f | grep -c "<valgrindoutput>"`
	end_num=`cat $f | grep -c "</valgrindoutput>"`

	if [[ $start_num != $end_num ]]; then
		echo "Fixing $f"
		sed  -i -e '0,/<\/valgrindoutput>/{//d;}' $f
	fi
done
