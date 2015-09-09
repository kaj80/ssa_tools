#!/bin/bash

LOG_DIR=$1

if [[ -z $LOG_DIR ]]; then
	echo "Usage: $(basename $0) <log dir>"
	exit 0
fi

if [[ ! -d $LOG_DIR ]]; then
	echo "Specified dir ($LOG_DIR) doesn't exist"
	exit 1
fi

# enable extended pattern matching operators (for 'rm' command)
shopt -s extglob

for layer in core distrib access acm
do
	if [[ $layer == "acm" ]]; then
		log_file="ibacm.log"
	else
		log_file="ibssa.log"
	fi

	pushd $LOG_DIR/$layer > /dev/null

	rm -f *.info
	for dir in `ls .`
	do
		rm -rf $dir/!($log_file)
	done

	popd > /dev/null
done
