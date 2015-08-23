#!/bin/bash


SSA_HOSTS_ADDR_FILE="${SSA_HOSTS_ADDR_FILE:-ssa.hosts.ipaddr}"

cat $SSA_HOSTS_ADDR_FILE | while read line; do
	ip=$(echo $line | awk '{print $2}')
	host=$(echo $line | awk '{print $1}')	    

	sudo pdsh -w $host "
		
		if ibportstate -D 0 1 | grep -q LinkUp; then

			ifconfig ib0 $ip netmask 255.255.0.0

		elif ibportstate -D 0 2 | grep -q LinkUp; then

			ifconfig ib1 $ip netmask 255.255.0.0

		fi
	"
	#echo "ifconfig $interface $ip netmask 255.255.0.0"
done
