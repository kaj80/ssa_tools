#!/bin/bash

input_files=""
ip_prefix=${SSA_IP_PREFIX:-"100.0.0."}
ipv6_prefix=${SSA_IPV6_PREFIX:-"fec0::"}

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

	ip_num=${ip_num##0}

	( printf "%-25s $ip_prefix$ip_num\t\t$ipv6_prefix$ip_num%s\n" "$line")
done

exit 0
