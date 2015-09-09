#!/bin/bash

hostname_input_file="${hostname_input_file:-ssa.hosts}"

hostdata_output_file="${hostdata_output_file:-/etc/rdma/ibssa_hosts.data}"

echo ""  | tr -d '\n' > $hostdata_output_file

while read line; do

	ssh -n $line '

	output_directory=/etc/rdma
	ip_file=/tmp/ip
	flags_file=/tmp/flags
	QP_file=/tmp/QP
	GID_file=/tmp/GID

	mkdir -p $output_directory

	if ibportstate -D 0 1 | grep -q "LinkUp"; then

		port_name=ib0

	elif ibportstate -D 0 2 | grep -q "LinkUp"; then

		port_name=ib1

	fi


	ip address show dev $port_name | grep "inet " | awk '\''{print $2}'\'' | cut -f1 -d'\''/'\'' > $ip_file

	(echo "0x" ; ip address show dev $port_name | grep infiniband | awk '\''{print $2}'\'' | cut -f1 -d'\'':'\'' ; ) | tr -d '\''\n'\'' > $flags_file

	(echo "0x" ; ip address show dev $port_name | grep infiniband | awk '\''{print $2}'\'' | tr - : | cut -f2-4 -d'\'':'\'' ; ) | tr -d '\'':\n'\'' > $QP_file

	ibaddr | awk '\''{print $2}'\'' > $GID_file

	( ( cat /tmp/ip ; echo -e '\''\t\t'\'' ; cat /tmp/GID ; echo -e  '\''\t'\'' ; cat /tmp/QP ; echo -e '\''\t'\'' ; cat /tmp/flags ) | tr -d '\''\n'\''  ; echo '\'''\'' ; )
	' >> $hostdata_output_file

done < $hostname_input_file



while read line; do

	scp $hostdata_output_file root@$line:$hostdata_output_file

done < $hostname_input_file

exit 0
