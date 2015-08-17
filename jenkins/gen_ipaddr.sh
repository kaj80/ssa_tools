#!/bin/bash

input_files=""
ip_prefix=${SSA_IP_PREFIX:-"100.0.0."}

for var in "$@"
do
	if [ ! -f $var ]; then
		echo "Non-existing input file specified: $var"
		exit 1
	fi
	input_files="$input_files $var"
done

if [[ -z $input_files ]]; then
	echo "No input files specified"
	exit 0
fi

rm -f $output_file

cat $input_files | while read line; do

        ip_num=$(echo $line | tr -dc '0-9')

	( printf "%-20s $ip_prefix%s\n" "$line" "${ip_num##0}" )
done

exit 0
