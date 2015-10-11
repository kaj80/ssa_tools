#!/bin/bash

input_files=""
ip_prefix=${SSA_IP_PREFIX:-"100.0"}
ip6_prefix=${SSA_IPV6_PREFIX:-"fec0::"}

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

cat $input_files | while read line; do

	[ -z "$line" ] && continue

        ip_num=$(echo $line | tr -dc '0-9' | sed 's/^0*//')

	if (( $ip_num < 255 )); then
		rem=0
		res=$ip_num
        elif (( $ip_num == 255 )); then
                rem=1
		res=0
	else
		rem=$((ip_num % 255))
		res=$((ip_num / 255))
	fi

	ip=$ip_prefix.$rem.$res

	( printf "%-25s $ip\t\t$ip6_prefix$ip_num%s\n" "$line")
done

exit 0
