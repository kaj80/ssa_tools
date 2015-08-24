#!/bin/bash

PROGNAME=$(basename $0)
OPENSM=${OPENSM:-"/sashakot/usr/sbin/opensm"}
SSADMIN=${SSADMIN:-"/sashakot/usr/sbin/ssadmin"}
OPENSM_CORE_CONF=${OPENSM_CORE_CONF:-"/sashakot/opensm.conf"}
OPENSM_NO_CORE_CONF=${OPENSM_NO_CORE_CONF:-""}a
RDMA_CONF_DIR=${RDMA_CONF_DIR:="/sashakot/usr/etc/rdma/"}
CORE_CONF=${CORE_CONF:-"$RDMA_CONF_DIR/ibssa_core_opts.cfg"}
ADDR_DATA_FILE=${ADDR_DATA_FILE:-"$RDMA_CONF_DIR/ibssa_hosts.data"}
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


function error_exit
{
	echo "$PROGRAME: ${1:-"Unknow Error"}" 1>&2
}


function get_rtrn()
{
	if (( $# < 2 )); then
		error_exit "ERROR - ${FUNCTION} wrong number of parameters"
	fi
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
	LOCAL_GID=`sudo ibaddr | cut -f2 -d" "`; rc=$?
	if (( $rc != 0 )) || [[ -z $LOCAL_GID ]]; then
		error_exit "ERROR - can't get local GID"
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
		error_exit "ERROR - switch is not found"
	fi

	let port_num=`sudo ibnetdiscover --Switch_list | grep "$SWITCH_GID_FOR_RESET" |cut -f5 -d" "`; rc=$?
	if (( $rc != 0 )) || [ 0 == $port_num ]; then
		error_exit "ERROR - can't find number of ports in switch "$SWITCH_GID_FOR_RESET
	fi

	for i in `seq 1 $port_num`; do
		if ibportstate --Guid $SWITCH_GID_FOR_RESET $i | grep -q "LinkUp"; then
			let SWITCH_PORT_FOR_RESET=$i
			break;
		fi
	done

	if [[ 0 == $SWITCH_PORT_FOR_RESET ]]; then
		error_exit "ERROR - port for reset is not found"
	fi

	echo $SWITCH_PORT_FOR_RESET
	echo $SWITCH_GID_FOR_RESET
}

generate_pr_update ()
{
	ibportstate --Guid $SWITCH_GID_FOR_RESET $SWITCH_PORT_FOR_RESET reset >> /dev/null
}

generate_ip_update ()
{
	touch $ADDR_DATA_FILE
	sudo pkill -HUP opensm
}

find_down_node ()
{
	if [[ $# == 0 ]]; then
		error_exit "ERROR - ${FUNCTION} called without input parameters"
	fi

	if [[ -z $1 ]]; then
		error_exit "ERROR - ${FUNCTION} the first parameter should be valid IB GID"
	fi

	local down_connection=`sudo $SSADMIN -g $1 --format=down nodeinfo | head -1`
	if [[ -z $down_connection ]]; then
		error_exit "ERROR - there is no downstream connection"
	fi

	local let down_node_lid=`echo $down_connection | cut -f2 -d" "`; rc=$?
	if (( $rc != 0)) || [[ 0 == $down_node_lid ]]; then
		error_exit "ERROR - there is no downstream connection"
	fi

	local down_node_gid=`echo $down_connection | cut -f1 -d" "`; rc=$?
	if (( $rc != 0)) || [[ -z $down_node_gid ]]; then
		error_exit "ERROR - there is no downstream connection"
	fi

	local down_node_type=`sudo $SSADMIN  -t -1 -g $down_node_gid  --format=short nodeinfo`; rc=$?
	if (( $rc != 0 )) || [[ -z $down_node_type ]]; then
		error_exit "ERROR - can't access node "$down_node_type
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

get_epochs ()
{
	if [[ $# == 0 ]]; then
		error_exit "ERROR - ${FUNCTION} called without input parameters"
	fi

	if [[ -z $1 ]]; then
		error_exit "ERROR - ${FUNCTION} the first parameter should be valid IB GID"
	fi

	local epochs=`sudo $SSADMIN -g $1 stats DB_EPOCH IPV4_EPOCH IPV6_EPOCH NAME_EPOCH`; rc=$?

	if (( $rc != 0 )) || [[ -z $epochs ]]; then
		error_exit "ERROR - can't access node "$1
	fi

	local let db_epoch=`echo "$epochs" | grep "DB_EPOCH" | cut -f2 -d" "`
	local let ipv4_epoch=`echo "$epochs" | grep "IPV4_EPOCH"  | cut -f2 -d" "`
	local let ipv6_epoch=`echo "$epochs" | grep "IPV6_EPOCH"  | cut -f2 -d" "`
	local let name_epoch=`echo "$epochs" | grep "NAME_EPOCH" | cut -f2 -d" "`

	echo $db_epoch,$ipv4_epoch,$ipv6_epoch,$name_epoch
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

	if [[ -z $result ]]; then
		echo "WARNING - a node don't have any downstream connection "$LOCAL_GID
		return
	fi

	let lid=`get_rtrn $result 1`
	gid=`get_rtrn $result 2`
	t=`get_rtrn $result 3`

	if [[ -z $t ]] || [[ -z $gid ]] || (( $lid < 0)); then
		error_exit "ERROR - Wrong ssadmin output "$result

	fi

	if [[ $t == "Core" ]]; then
		error_exit "ERROR - Core has a core node as downstream connection"
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

	if [[ -z $result ]]; then
		echo "WARNING - a node don't have any downstream connection "$gid
		return
	fi

	let lid=`get_rtrn $result 1`
	gid=`get_rtrn $result 2`
	t=`get_rtrn $result 3`

	if [[ -z $t ]] || [[ -z $gid ]] || (( $lid < 0)); then
		error_exit "ERROR - Wrong ssadmin output "$result

	fi

	if [[ $t == "Core" ]] || [[ $t == "Distrib" ]]; then
		error_exit "ERROR - Wrong type of downstream connection "$t" "$gid" "$lid
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

	if [[ -z $result ]]; then
		echo "WARNING - a node don't have any downstream connection "$gid
		return
	fi

	let lid=`get_rtrn $result 1`
	gid=`get_rtrn $result 2`
	t=`get_rtrn $result 3`

	if [[ -z $t ]] || [[ -z $gid ]] || (( $lid < 0)); then
		error_exit "ERROR - Wrong ssadmin output "$result

	fi

	if [[ $t == "Distrib" ]] || [[ $t == "Distrib" ]] || [[ $t == "Access" ]]; then
		error_exit "ERROR - Wrong type of downstream connection "$t" "$gid" "$lid
	fi

	if [[ $t == "ACM" ]]; then
		ACM_GID=$gid
		let ACM_LID=$lid

		return
	fi
}

get_local_port_number
get_local_gid
#start_core
find_port_for_reset
generate_pr_update
generate_ip_update 
find_ssa_nodes

echo "Distrib "$DISTRIB_GID" "$DISTRIB_LID
echo "Access "$ACCESS_GID" "$ACCESS_LID
echo "ACM "$ACM_GID" "$ACM_LID

get_epochs $LOCAL_GID
if [[ ! -z $DISTRIB_GID ]];then
	get_epochs $DISTRIB_GID
fi

if [[ ! -z $ACCESS_GID ]];then
	get_epochs $ACCESS_GID
fi

if [[ ! -z $ACM_GID ]];then
	get_epochs $ACM_GID
fi
