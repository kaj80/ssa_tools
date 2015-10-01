#!/bin/bash


SSA_HOSTS_ADDR_FILE="${SSA_HOSTS_ADDR_FILE:-ssa.hosts.ipaddr}"

cat $SSA_HOSTS_ADDR_FILE | while read line; do
	ip=$(echo $line | awk '{print $2}')
	ipv6=$(echo $line | awk '{print $3}')
	host=$(echo $line | awk '{print $1}')

	sudo pdsh -w $host "

		if ibportstate -D 0 1 | grep -q LinkUp; then

			ifconfig ib0 $ip netmask 255.255.0.0

		elif ibportstate -D 0 2 | grep -q LinkUp; then

			ifconfig ib1 $ip netmask 255.255.0.0

		fi

		echo $ipv6 > /tmp/my_ipv6
	"

	sudo pdsh -w $host '


		if ibportstate -D 0 1 | grep -q LinkUp; then

			interface=ib0

		else

			interface=ib1

		fi

		correct_addr=`cat /tmp/my_ipv6`

		suffix=/64

		correct_addr=$correct_addr$suffix

		ip addr show dev $interface | grep '\''inet6'\'' | while read line; do

			ipv6_addr=`echo $line | awk '\''{print $2}'\''`

			ip -6 addr del $ipv6_addr dev $interface

		done

		ip -6 addr add $correct_addr dev $interface

	'
done
