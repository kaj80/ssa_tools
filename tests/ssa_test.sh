#!/bin/bash

OPENSM=${OPENSM:-"/sashakot/usr/sbin/opensm"}
OPENSM_CORE_CONF=${OPENSM_CORE_CONF:-"/sashakot/opensm.conf"}
OPENSM_NO_CORE_CONF=${OPENSM_NO_CORE_CONF:-""}
OPENSM_DEFAULT_PRIORITY=7
CORE_LOG=${CORE_LOG:-"/var/log/ibssa.log"}
LOCAL_PORT_NUM=0

start_core ()
{
	sudo pkill -9 opensm
	sudo $OPENSM -F $OPENSM_CORE_CONF -B --priority $OPENSM_DEFAULT_PRIORITY

}

get_local_port_number ()
{
	if  ibportstate -D 0 1 | grep -q "LinkUp"; then
		let LOCAL_PORT_NUM=1
	elif ibportstate -D 0 2 | grep -q "LinkUp"; then
		let LOCAL_PORT_NUM=2
	fi

}

generate_sm_hadover ()
{
	sudo ibportstate -D 0 $LOCAL_PORT_NUM reset
}

find_host_for_update ()
{
	switch_gid=`sudo ibnetdiscover --Switch_list | head -1 | cut -f3 -d" "`
	if [[ -z $switch_gid ]]; then
		echo "ERROR - switch is not found"
		exit
	fi

	let port_num=`sudo ibnetdiscover --Switch_list | grep "$switch_gid" |cut -f5 -d" "`
	if [[ 0 == $port_num ]]; then
		echo "ERROR - can't find number of ports in switch "$switch_gid
		exit
	fi
	echo $switch_gid
	echo $port_num
}

echo $OPENSM
echo $OPENSM_CORE_CONF
echo $OPENSM_NO_CORE_CONF
echo $OPENSM_DEFAULT_PRIORITY

get_local_port_number
echo $LOCAL_PORT_NUM
#start_core
find_host_for_update
