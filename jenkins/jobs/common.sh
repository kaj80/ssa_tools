#!/bin/bash

function welcome_print() {
	echo "Path env variable: $PATH"
	echo "Workspace path: $WORKSPACE"
	echo "Starting on host: $(hostname)"
}

function node_is_used() {
	rc=1

	for node in $NODES_UNUSED
	do
	    if [ $NODE_NAME == $node ]; then
		rc=0
		break
	    fi
	done

	echo $rc
}

function stop_ssa() {
	sudo pkill -9 opensm
	sudo pkill -9 ibssa
	sudo pkill -9 ibacm

	sudo pkill -9 riostream
	sudo pkill -9 rstream
}

function get_node_label() {
	node_label=""

	for label in $NODE_LABELS
	do
		if [ $label == "MOFED" ] || [ $label == "UPSTR" ]; then
			node_label=$label
			break
		fi
	done

	echo $node_label
}
