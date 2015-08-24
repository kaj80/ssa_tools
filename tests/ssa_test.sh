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
SSADMIN_TIMEOUT=${SSADMIN_TIMEOUT:-" "}
CORE_LOG=${CORE_LOG:-"/var/log/ibssa.log"}
LOCAL_PORT_NUM=0
SWITCH_GID_FOR_RESET=""
let SWITCH_PORT_FOR_RESET=0
CORE_GID=""
CORE_LID=""
DISTRIB_GID=""
DISTRIB_LID=""
ACCESS_GID=""
ACCESS_LID=""
ACM_GID=""
ACM_LID=""


function error_exit
{
	echo "$PROGRAME: ${1:-"Unknow Error"}" 1>&2
	exit 1
}


function get_rtrn
{
	if (( $# < 2 )); then
		error_exit "ERROR - ${FUNCTION} wrong number of parameters"
	fi
	echo `echo $1 | cut --delimiter=, -f $2`
}

function start_core
{
	sudo pkill -9 opensm
	sudo $OPENSM -F $OPENSM_CORE_CONF -B --priority $OPENSM_DEFAULT_PRIORITY
}

function get_local_port_number
{
	if  ibportstate -D 0 1 | grep -q "LinkUp"; then
		let LOCAL_PORT_NUM=1
	elif ibportstate -D 0 2 | grep -q "LinkUp"; then
		let LOCAL_PORT_NUM=2
	fi
}

function get_local_gid
{
	local tmp=`sudo ibaddr`; rc=$?

	if (( $rc != 0 )); then
		error_exit "ERROR - can't get local GID"
	fi

	CORE_GID=`echo $tmp | cut -f2 -d" "`
	if [[ -z $CORE_GID ]]; then
		error_exit "ERROR - can't get local GID"
	fi

	local  hex_lid=`echo $tmp | cut -f5 -d" " `
	CORE_LID=`printf '%d' $hex_lid`
}

function generate_sm_hadover
{
	local -i rc
	sudo ibportstate -D 0 $LOCAL_PORT_NUM reset; rc=$?

	return $rc
}

function find_port_for_reset
{
	local -i rc

	SWITCH_GID_FOR_RESET=`sudo ibnetdiscover --Switch_list | head -1 | cut -f3 -d" "`; rc=$?
	if (( $rc != 0 )) || [[ -z $SWITCH_GID_FOR_RESET ]]; then
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

	return 0
}

function generate_pr_update
{
	local -i rc

	ibportstate --Guid $SWITCH_GID_FOR_RESET $SWITCH_PORT_FOR_RESET reset >> /dev/null; rc=$?

	if (( $rc != 0 )); then
		error_exit "ERROR -ibportstate failed"
	fi

	return 0
}

function generate_ip_update
{
	touch $ADDR_DATA_FILE
	sudo pkill -HUP opensm
}

function find_down_node
{
	local -i rc=0

	if [[ $# == 0 ]]; then
		error_exit "ERROR - ${FUNCTION} called without input parameters"
	fi

	if [[ -z $1 ]]; then
		error_exit "ERROR - ${FUNCTION} the first parameter should be valid IB GID"
	fi

	local down_connection=`$SSADMIN $SSADMIN_TIMEOUT -g $1 --format=down nodeinfo | head -1`
	if (( $rc != 0 )) || [[ -z $down_connection ]]; then
		error_exit "ERROR - there is no downstream connection"
	fi

	local let down_node_lid=`echo $down_connection | cut -f2 -d" "`; rc=$?
	if (( $rc != 0)) || (( 0 > $down_node_lid )); then
		error_exit "ERROR - there is no downstream connection"
	fi

	local down_node_gid=`echo $down_connection | cut -f1 -d" "`; rc=$?
	if (( $rc != 0)) || [[ -z $down_node_gid ]]; then
		error_exit "ERROR - there is no downstream connection"
	fi

	local down_node_type=`$SSADMIN $SSADMIN_TIMEOUT -g $down_node_gid --format=short nodeinfo`; rc=$?
	if (( $rc != 0 )) || [[ -z $down_node_type ]]; then
		error_exit "ERROR - can't access node "$down_node_gid
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

	return 0
}

function get_epochs
{
	local -i rc

	if [[ $# == 0 ]]; then
		error_exit "ERROR - ${FUNCTION} called without input parameters"
	fi

	if [[ -z $1 ]]; then
		error_exit "ERROR - ${FUNCTION} the first parameter should be valid IB GID"
	fi

	local epochs=`sudo $SSADMIN $SSADMIN_TIMEOUT -g $1 stats DB_EPOCH IPV4_EPOCH IPV6_EPOCH NAME_EPOCH`; rc=$?

	if (( $rc != 0 )) || [[ -z $epochs ]]; then
		error_exit "ERROR - can't access node "$1
	fi

	local let db_epoch=`echo "$epochs" | grep "DB_EPOCH" | cut -f2 -d" "`
	local let ipv4_epoch=`echo "$epochs" | grep "IPV4_EPOCH"  | cut -f2 -d" "`
	local let ipv6_epoch=`echo "$epochs" | grep "IPV6_EPOCH"  | cut -f2 -d" "`
	local let name_epoch=`echo "$epochs" | grep "NAME_EPOCH" | cut -f2 -d" "`

	echo $db_epoch" "$ipv4_epoch" "$ipv6_epoch" "$name_epoch

	return 0
}


function find_ssa_nodes
{
	local -i rc=0
	DISTRIB_GID=""
	DISTRIB_LID=""
	ACCESS_GID=""
	ACCESS_LID=""
	ACM_GID=""
	ACM_LID=""

	local lid
	local gid
	local t
	local result=""

	let lid=0
	let ACM_LID=0
	let ACCESS_LID=0
	let DISTRIB_LID=0

	result=`find_down_node $CORE_GID`

	if (( $rc != 0 )) || [[ -z $result ]]; then
		echo "WARNING - a node don't have any downstream connection "$CORE_GID
		return 1
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

		return 1
	fi

	result=""
	result=`find_down_node $gid`; rc=$?

	if (( $rc != 0 )) || [[ -z $result ]]; then
		echo "WARNING - a node don't have any downstream connection "$gid
		return 1
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

		return 1
	fi

	result=""
	result=`find_down_node $gid`; rc=$?

	if (( $rc != 0 )) || [[ -z $result ]]; then
		echo "WARNING - a node don't have any downstream connection "$gid
		return 1
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

		return 1
	fi

	return 0
}

function get_iner_nodes_epochs ()
{
	local tmp

	tmp=`get_epochs $CORE_GID`
	echo "Core "$tmp

	if [[ ! -z $DISTRIB_GID ]];then
		tmp=`get_epochs $DISTRIB_GID`
		echo "Distrib "$tmp
	fi

	if [[ ! -z $ACCESS_GID ]];then
		tmp=`get_epochs $ACCESS_GID`
		echo "Access "$tmp
	fi

#	if [[ ! -z $ACM_GID ]];then
#		tmp=`get_epochs $ACM_GID`
#		echo "ACM "$tmp
#	fi
}

function print_ssa_nodes ()
{
	echo "Core "$CORE_GID" "$CORE_LID

	if [[ ! -z $DISTRIB_GID ]];then
		echo "Distrib "$DISTRIB_GID" "$DISTRIB_LID
	fi

	if [[ ! -z $ACCESS_GID ]];then
		echo "Access "$ACCESS_GID" "$ACCESS_LID
	fi

	if [[ ! -z $ACM_GID ]];then
		echo "ACM "$ACM_GID" "$ACM_LID
	fi
}

get_local_port_number
get_local_gid; rc=$?
if (( rc != 0 )); then
	exit $rc
fi
#start_core
find_port_for_reset
find_ssa_nodes
print_ssa_nodes
get_iner_nodes_epochs

generate_pr_update
generate_ip_update
