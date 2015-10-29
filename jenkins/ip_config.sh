#!/bin/bash


SSA_HOSTS_ADDR_FILE="${SSA_HOSTS_ADDR_FILE:-ssa.hosts.ipaddr}"

cat $SSA_HOSTS_ADDR_FILE | while read line; do
	ip=$(echo $line   | awk '{print $2}')
	ipv6=$(echo $line | awk '{print $3}')
	host=$(echo $line | awk '{print $1}')

	pdsh -w $host "/proj/SSA/Mellanox/ilyan/ip_config.sh $ip $ipv6"
done
