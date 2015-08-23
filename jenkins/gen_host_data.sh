#!/bin/bash

input_file="${input_file:-/tmp/jenkins/workspace/run_ssa/label/dev-r-vrt-030/nodes.list}"

hostname_file="${hostname_file:-/tmp/hostnames.list}"

output_file="${output_file:-/etc/rdma/ibssa_hosts.data}"

cat $input_file | awk '{print $1}' > $hostname_file

echo ""  | tr -d '\n' > $output_file

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
	' >> $output_file

done < $hostname_file



while read line; do

	scp $output_file root@$line:$output_file

done < $hostname_file

exit 0
