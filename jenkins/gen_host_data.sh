#!/bin/bash

hostname_input_file="${hostname_input_file:-ssa.hosts}"

hostdata_output_file="${hostdata_output_file:-/usr/local/etc/rdma/ibssa_hosts.data}"

echo ""  | tr -d '\n' > $hostdata_output_file

cat $hostname_input_file | while read line; do

	pdsh -N -w $line '

	if sudo ibportstate -D 0 1 | grep -q "LinkUp"; then

		interface=ib0

	elif sudo ibportstate -D 0 2 | grep -q "LinkUp"; then

		interface=ib1

	fi


	ip=$(sudo ip address show dev $interface | grep "inet " | awk '\''{print $2}'\'')
	ip=$(echo $ip | cut -f1 -d'\''/'\'')

	ipv6=$(sudo ip address show dev $interface | grep "inet6" | awk '\''{print $2}'\'')
	ipv6=$(echo $ipv6 | sed -n 1p | cut -f1 -d'\''/'\'')

	flags=`(echo "0x" ; sudo ip address show dev $interface | grep infiniband | awk '\''{print $2}'\'' | cut -f1 -d'\'':'\'' ; ) | tr -d '\''\n'\''`

	QP=`(echo "0x" ; sudo ip address show dev $interface | grep infiniband | awk '\''{print $2}'\'' | tr - : | cut -f2-4 -d'\'':'\'' ; ) | tr -d '\'':\n'\''`

	GID=`sudo ibaddr | awk '\''{print $2}'\''`

	printf "%-30s $GID\t\t$QP\t$flags\n" "$ip"
	printf "%-30s $GID\t\t$QP\t$flags\n" "$ipv6"

	' >> $hostdata_output_file

done



#while read line; do

#	scp $hostdata_output_file root@$line:$hostdata_output_file

#done < $hostname_input_file

exit 0
