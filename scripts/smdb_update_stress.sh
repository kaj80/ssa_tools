#!/bin/bash

iters=${1:-100}
prefix="/usr/local/"
addr_file="$prefix/etc/rdma/ibssa_hosts.data"

echo "--------------------- START SMDB UPDATE STRESS TEST -------------------"

for i in `seq 1 $iters`
do
	# Update address file
	touch $addr_file

	# Generate SUBNET UP event
	kill -s HUP `pidof opensm`

	# Query PRDB on ACM side
	stderr=$($prefix/sbin/ssadmin -r dbquery --filter=acm 2>&1 > /dev/null)
	if (( $? != 0 )); then
		echo "ERROR: unable to send dbquery, exiting ..."
		exit 1
	fi

	if [[ $stderr =~ .*POLLERR|POLLOUT.* ]]; then
		echo "$stderr"
		exit 1
	fi

	echo "Finished update #$i (output: $stderr)"
done

echo "--------------------- SMDB UPDATE STRESS TEST FINISHED -----------------"

exit 0
