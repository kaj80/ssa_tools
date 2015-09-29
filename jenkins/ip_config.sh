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

		has_site_addr=0

		suffix=/64


		ip addr show dev ib0 | grep '\''inet6'\'' | while read line; do

			if echo $line | grep -q '\''scope site'\''; then

				has_site_addr=1

			else

				ipv6_addr=`echo /tmp/my_ipv6 | tr -d '\''\n'\''`

				ip -6 addr del $ipv6_addr dev $port_name

			fi


		done

		if [ "$has_site_addr" = "0" ]; then
	

			ipv6_addr=`cat /tmp/my_ipv6 | tr -d '\''\n'\''`

			ipv6_addr=$ipv6_addr$suffix

			ip -6 addr add $ipv6_addr dev $port_name

		fi

	'
done
