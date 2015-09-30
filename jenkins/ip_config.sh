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

			port_name=ib0

		else

			port_name=ib1

		fi

		correct_addr=`cat /tmp/my_ipv6`

		has_correct_addr=0

		suffix=/64

		correct_addr=$correct_addr$suffix

		ip addr show dev $port_name | grep '\''inet6'\'' | while read line; do

			ipv6_addr=`echo $line | awk '\''{print $2}'\''`

			if [ "$ipv6_addr" = "$correct_addr" ]; then

				has_correct_addr=1

			else

				ip -6 addr del $ipv6_addr dev $port_name

			fi

		done

		if [ "$has_correct_addr" = "0" ]; then

			ip -6 addr add $correct_addr dev $port_name

		fi

	'
done
