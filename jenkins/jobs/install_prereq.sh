#!/bin/bash

. $(dirname $0)/common.sh

status=0

welcome_print

if [[ $(node_is_used) == 0 ]]; then
	echo "This node is not used ($NODE_NAME : $NODE_LABELS)."
	exit 0
fi

stop_ssa

install_type=$(get_node_label)

if [ $install_type == "UPSTR" ]; then
	echo "Executing UPSTREAM installation ..."
	upstream_dir="$WORKSPACE/upstream"

	[ -d $upstream_dir ] && rm -rf $upstream_dir
	mkdir -p $upstream_dir

	export SSA_DEST=$upstream_dir
	export SSA_LIBS_REPO="$LIBMLX4_REPO \
			      $LIBMLX5_REPO \
			      $LIBIBVERBS_REPO \
			      $LIBIBUMAD_REPO \
			      $OPENSM_REPO"

	./ssa_tools/ssa_setup.sh lib_download
	./ssa_tools/jenkins/simple_build.sh $upstream_dir
	status=$?
elif [ $install_type == "MOFED" ]; then
	if [ -z $MOFED_VERSION ]; then
		latest_ptr="latest"
	else
		latest_ptr="latest-${MOFED_VERSION}"
	fi
	echo "Executing MOFED installation ... `cat ${MOFED_SRC}/${latest_ptr}.txt`"

	[ -f /usr/sbin/ofed_uninstall.sh ] && /usr/sbin/ofed_uninstall.sh --force

	sudo build=${latest_ptr} ${MOFED_SRC}/mlnx_ofed_install ${MOFED_FLAGS}
	sudo /etc/init.d/openibd restart
else
	echo "Node with unknown labels ($NODE_NAME : $NODE_LABELS)"
	status=1
fi

exit $status
