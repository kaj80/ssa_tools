#!/bin/bash

argc=$#
if (( $argc != 4 )); then
    echo "Usage: $0 <nodes_file> <topology_file> <node_type: core/distrib/access/acm> <label for filtering>"
    exit 0
fi

node_file=$1
topo_file=$2
node_type=$3
node_label=$4

selected_node_list=$(cat $node_file | grep $node_label | cut -d" " -f1)
output="${node_type}_nodes "

for node in $selected_node_list
do
    ret="`cat $topo_file | grep $node_type | grep $node`"
    if [[ -z $ret ]]; then
        continue
    fi

    output="${output}${node},"
done

cat $topo_file | grep -v $node_type
echo ${output%,}

exit 0
