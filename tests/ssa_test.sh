#!/bin/bash

OPENSM=${OPENSM:-"/sashakot/usr/sbin/opensm"}
SSADMIN=${SSADMIN:-"/sashakot/usr/sbin/ssadmin"}
OPENSM_CORE_CONF=${OPENSM_CORE_CONF:-"/sashakot/opensm.conf"}
OPENSM_NO_CORE_CONF=${OPENSM_NO_CORE_CONF:-""}
OPENSM_DEFAULT_PRIORITY=7
CORE_LOG=${CORE_LOG:-"/var/log/ibssa.log"}
LOCAL_PORT_NUM=0
SWITCH_GID_FOR_RESET=""
let SWITCH_PORT_FOR_RESET=0
LOCAL_GID=""
DISTRIB_GID=""
DISTRIB_LID=""
ACCESS_GID=""
ACCESS_LID=""
ACM_GID=""
ACM_LID=""

function get_rtrn()
{
	echo `echo $1 | cut --delimiter=, -f $2`
}

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

get_local_gid ()
{
	LOCAL_GID=`sudo ibaddr | cut -f2 -d" "`
	if [[ -z $LOCAL_GID ]]; then
		echo "ERROR - can't get local GID"
		exit
	fi
}

generate_sm_hadover ()
{
	sudo ibportstate -D 0 $LOCAL_PORT_NUM reset
}

find_port_for_reset ()
{
	SWITCH_GID_FOR_RESET=`sudo ibnetdiscover --Switch_list | head -1 | cut -f3 -d" "`
	if [[ -z $SWITCH_GID_FOR_RESET ]]; then
		echo "ERROR - switch is not found"
		exit
	fi

	let port_num=`sudo ibnetdiscover --Switch_list | grep "$SWITCH_GID_FOR_RESET" |cut -f5 -d" "`
	if [[ 0 == $port_num ]]; then
		echo "ERROR - can't find number of ports in switch "$SWITCH_GID_FOR_RESET
		exit
	fi

	for i in `seq 1 $port_num`; do
		if ibportstate --Guid $SWITCH_GID_FOR_RESET $i | grep -q "LinkUp"; then
			let SWITCH_PORT_FOR_RESET=$i
			break;
		fi
	done

	if [[ 0 == $SWITCH_PORT_FOR_RESET ]]; then
		echo "ERROR - port for reset is not found"
		exit;
	fi

	echo $SWITCH_PORT_FOR_RESET
	echo $SWITCH_GID_FOR_RESET
}

generate_pr_update ()
{
	ibportstate --Guid $SWITCH_GID_FOR_RESET $SWITCH_PORT_FOR_RESET reset >> /dev/null
}

find_down_node ()
{
	if [[ $# == 0 ]]; then
		echo "ERROR - ${FUNCTION} called without input parameters"
		exit
	fi

	if [[ -z $1 ]]; then
		echo "ERROR - ${FUNCTION} the first parameter should be valid IB GID"
		exit
	fi

	local down_connection=`sudo $SSADMIN -g $1 --format=down nodeinfo | head -1`
	if [[ -z $down_connection ]]; then
		echo "ERROR - there is no downstream connection"
		exit
	fi

	local let down_node_lid=`echo $down_connection | cut -f2 -d" "`
	if [[ 0 == $down_node_lid ]]; then
		echo "ERROR - there is no downstream connection"
		exit
	fi

	local down_node_gid=`echo $down_connection | cut -f1 -d" "`
	if [[ -z $down_node_gid ]]; then
		echo "ERROR - there is no downstream connection"
		exit
	fi

	local down_node_type=`sudo $SSADMIN  -t -1 -g $down_node_gid  --format=short nodeinfo`
	if [[ -z $down_node_type ]]; then
		echo "ERROR - can't access node "$down_node_type
		exit
	fi

	if echo $down_node_type | grep -q "Core"; then
		down_node_type="Core"
	elif echo $down_node_type | grep -q "Access"; then
		down_node_type="Access"
	elif echo $down_node_type | grep -q "Distribution"; then
		down_node_type="Distrib"
	else
		down_node_type="ACM"
	fi

	echo $down_node_lid,$down_node_gid,$down_node_type
}

find_ssa_nodes ()
{
	DISTRIB_GID=""
	DISTRIB_LID=""
	ACCESS_GID=""
	ACCESS_LID=""
	ACM_GID=""
	ACM_LID=""

	local lid
	local gid
	local t
	local result

	let lid=0
	let ACM_LID=0
	let ACCESS_LID=0
	let DISTRIB_LID=0

	result=`find_down_node $LOCAL_GID`
	echo $result

	if [[ -z $result ]]; then
		echo "ERROR - a node don't have any downstream connection "$LOCAL_GID
	fi

	let lid=`get_rtrn $result 1`
	gid=`get_rtrn $result 2`
	t=`get_rtrn $result 3`

	if [[ $t == "Core" ]]; then
		echo "ERROR - Core has a core node as downstream connection"
		exit
	fi

	if [[ $t == "Distrib" ]]; then
		DISTRIB_GID=$gid
		let DISTRIB_LID=$lid
	fi

	if [[ $t == "Access" ]]; then
		ACCESS_GID=$gid
		let ACCESS_LID=$lid
	fi

	if [[ $t == "ACM" ]]; then
		ACM_GID=$gid
		let ACM_LID=$lid

		return
	fi

	result=`find_down_node $gid`
	echo $result

	if [[ -z $result ]]; then
		return
	fi

	let lid=`get_rtrn $result 1`
	gid=`get_rtrn $result 2`
	t=`get_rtrn $result 3`

	if [ $t == "Distrib" ] || [ $t == "Distrib" ]; then
		echo "ERROR - Wrong type of downstream connection "$t" "$gid" "$lid
		exit
	fi

	if [[ $t == "Access" ]]; then
		ACCESS_GID=$gid
		let ACCESS_LID=$lid
	fi

	if [[ $t == "ACM" ]]; then
		ACM_GID=$gid
		let ACM_LID=$lid

		return
	fi

	result=`find_down_node $gid`
	echo $result

	if [[ -z $result ]]; then
		return
	fi

	let lid=`get_rtrn $result 1`
	gid=`get_rtrn $result 2`
	t=`get_rtrn $result 3`

	if [ $t == "Distrib" ] || [ $t == "Distrib" ] || [ $t == "Access" ]; then
		echo "ERROR - Wrong type of downstream connection "$t" "$gid" "$lid
		exit
	fi

	if [[ $t == "ACM" ]]; then
		ACM_GID=$gid
		let ACM_LID=$lid

		return
	fi
}

echo $OPENSM
echo $OPENSM_CORE_CONF
echo $OPENSM_NO_CORE_CONF
echo $OPENSM_DEFAULT_PRIORITY
echo $SSADMIN

get_local_port_number
get_local_gid
echo $LOCAL_PORT_NUM
echo $LOCAL_GID
#start_core
find_port_for_reset
generate_pr_update
find_ssa_nodes

echo "Distrib "$DISTRIB_GID" "$DISTRIB_LID
echo "Access "$ACCESS_GID" "$ACCESS_LID
echo "ACM "$ACM_GID" "$ACM_LID

