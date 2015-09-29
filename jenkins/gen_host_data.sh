#!/bin/bash

hostname_input_file="${hostname_input_file:-ssa.hosts}"

hostdata_output_file="${hostdata_output_file:-/etc/rdma/ibssa_hosts.data}"

echo ""  | tr -d '\n' > $hostdata_output_file

while read line; do

	ssh -n $line '

	output_directory=/etc/rdma

	ipv6="F"

	mkdir -p $output_directory

	if ibportstate -D 0 1 | grep -q "LinkUp"; then

		port_name=ib0

	elif ibportstate -D 0 2 | grep -q "LinkUp"; then

		port_name=ib1

	fi


	ip=`ip address show dev $port_name | grep "inet " | awk '\''{print $2}'\''` # retrieve ip
	ip=`echo $ip | cut -f1 -d'\''/'\''` # get rid of irrelevant part

	ipv6=`ip address show dev $port_name | grep "inet6" | awk '\''{print $2}'\''`
	ipv6=`echo $ipv6 | sed -n 1p | cut -f1 -d'\''/'\''`

	flags=`(echo "0x" ; ip address show dev $port_name | grep infiniband | awk '\''{print $2}'\'' | cut -f1 -d'\'':'\'' ; ) | tr -d '\''\n'\''`

	QP=`(echo "0x" ; ip address show dev $port_name | grep infiniband | awk '\''{print $2}'\'' | tr - : | cut -f2-4 -d'\'':'\'' ; ) | tr -d '\''\n'\''`

	GID=`ibaddr | awk '\''{print $2}'\''`

	#output:
	( printf "%-30s $GID\t\t$QP\t$flags%s\n" "$ip" ;
		printf "%-30s $GID\t\t$QP\t$flags%s\n" "$ipv6" ; )

	' >> $hostdata_output_file
	' >> $hostdata_output_file

done < $hostname_input_file



while read line; do

	scp $hostdata_output_file root@$line:$hostdata_output_file

done < $hostname_input_file

exit 0
