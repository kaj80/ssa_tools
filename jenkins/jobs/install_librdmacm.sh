#!/bin/bash

. $(dirname $0)/common.sh

welcome_print

if [[ $(node_is_used) == 0 ]]; then
	echo "This node is not used ($NODE_NAME : $NODE_LABELS)."
	exit 0
fi

stop_ssa

install_type=$(get_node_label)

if [ $install_type == "UPSTR" ]; then
	echo "Executing UPSTREAM librdmacm installation ..."
	upstream_dir="$WORKSPACE/upstream"
	[ -d $upstream_dir ] && rm -rf $upstream_dir
	mkdir -p $upstream_dir

	cd $upstream_dir

	ret=1
	while [ $ret -ne 0 ];
	do
		echo "Cloning $LIBRDMACM_UPSTR_REPO ..."
		git clone $LIBRDMACM_UPSTR_REPO
		ret=$?
		if [ $ret -eq 0 ]; then
			echo "Cloning succeded."
		fi
	done

	cd $WORKSPACE
	$(dirname $0)/../simple_build.sh $upstream_dir
elif [ $install_type == "MOFED" ]; then
	if [ -z $MOFED_VERSION ]; then
		latest_ptr="latest"
	else
		latest_ptr="latest-${MOFED_VERSION}"
	fi

	echo "Executing MOFED librdmacm installation ... `cat ${MOFED_SRC}/${latest_ptr}.txt`"

	[ -f /usr/sbin/ofed_uninstall.sh ] && /usr/sbin/ofed_uninstall.sh --force

	sudo build=${latest_ptr} ${MOFED_SRC}/mlnx_ofed_install ${MOFED_FLAGS}
	sudo /etc/init.d/openibd restart

	mofed_dir="$WORKSPACE/mofed"
	[ -d $mofed_dir ] && rm -rf $mofed_dir
	mkdir -p $mofed_dir

	cd $mofed_dir
	git clone $LIBRDMACM_MOFED_REPO

	cd $WORKSPACE
	$(dirname $0)/../simple_build.sh $mofed_dir
else
	echo "Node with unknown labels ($NODE_NAME : $NODE_LABELS)"
fi
