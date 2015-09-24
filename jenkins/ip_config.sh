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

	sudo pdsh -w $host '

		gid_file=/tmp/config_gid

		ipv6_file=/tmp/config_IPv6

		if ibportstate -D 0 1 | grep -q LinkUp; then

			port_name=ib0

		else

			port_name=ib1

		fi

		ibaddr | awk '\''{print $2}'\'' | tr -d '\''\n'\''  > $gid_file

		(cat $gid_file | cut -f1 -d'\'':'\'' ; echo ::202: ; cat $gid_file | cut -f4-6 -d'\'':'\'') | tr -d '\''\n'\'' > $ipv6_file

		if ! ip addr show dev $port_name | grep -q inet6; then

			ifconfig $port_name inet6 add `cat $ipv6_file`/64
		fi

	'
done
