#!/bin/bash

export PATH=/.autodirect/app/bullseye/bin/:$PATH
ME=`basename $0`
MY_DIR=`dirname $0`

if [[ $# > 0 ]];then
	TOPOLOGY=$1;
else
	echo "ERROR: There is topology file name"
	echo "Usage: $ME <topology_file_name> <coverage_report_folder>"
	exit 1
fi

if [[ $# > 1 ]];then
	INPUT_FOLDER=$2;
else
	echo "ERROR: There folder with coverage reports"
	echo "Usage: $ME <topology_file_name> <coverity_report_folder>"
	exit 1
fi

if [ ! -f $TOPOLOGY ]; then
    echo "Topology file is not found. $TOPOLOGY"
    exit 1
fi

if [ ! -d $INPUT_FOLDER ]; then
    echo "Input folder is not found. $INPUT_FOLDER"
    exit 1
fi

for node_type in core distrib access acm; do
    node_label=$node_type"_nodes"
    exclude_file=$MY_DIR/$node_type".BullseyeCoverageExclusions"
    echo "Process $node_type"
    if [ -f $exclude_file ]; then
    	echo "Apply $exclude_file for"
    	nodes_list=`cat $TOPOLOGY|awk "/$node_label/{print"' $2}'`
	nodes_list=${nodes_list//,/ }
    	echo "$nodes_list nodes"
	for node_name in $nodes_list; do
		cov_file=$INPUT_FOLDER"/"$node_name".cov"
		if [ -f $cov_file ]; then
			covselect -a -f $cov_file -i $exclude_file ;rc=$?
			if [ $rc -ne 0 ]; then
				echo "ERROR: covselect -i $exclude_file -a -f $cov_file faled"
			fi
		fi
	done
    fi
done
