#!/bin/bash

CFLAGS=${CFLAGS-"-g -O0 -rdynamic -DREMOTE_FLAGS_MASK=0xE0"}

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
	OPTFLAGS=""
elif [ $install_type == "MOFED" ]; then
	# due to MOFED version of OpenSM that is installed into /usr and not /usr/local
	OPTFLAGS="--includedir=/usr/include"
else
	echo "Node with unknown labels ($NODE_NAME : $NODE_LABELS)"
	exit 1
fi

echo "Executing SSA installation ..."

src_dir="$WORKSPACE/ibssa2"
if [ ! -d $src_dir ]; then
    echo "ERROR - SSA sources directory ($src_dir) doesn't exists. Exiting ..."
    exit 1
fi

cd $src_dir
export PATH=/.autodirect/app/bullseye/bin/:$PATH
export COVAPPDATADIR=/tmp/.BullseyeCoverage
#git_short=`git rev-parse --short HEAD`
export COVFILE=/tmp/`hostname`.cov
export COVSRCDIR=$WORKSPACE/ibssa2
export COVCCFG=$WORKSPACE/covc.cfg
echo "--symbolic" > $COVCCFG
sudo rm -f $COVFILE
covselect -i $WORKSPACE/ssa_tools/jenkins/ssa_cov_exclude
cov01 -1
./autogen.sh && ./configure CFLAGS="$CFLAGS" $OPTFLAGS && make clean && make -j && sudo -E make install
rc=$?

cov01 -0

if [[ $rc != 0 ]]; then
       echo "ERROR: SSA compilation failed"
       exit $rc
fi

# Installing configuration files
conf_dir=/usr/local/etc/rdma
sudo rm -rf $conf_dir
sudo mkdir -p $conf_dir
sudo cp $src_dir/plugin/ibssa_core_opts.cfg	$conf_dir/
sudo cp $src_dir/distrib/ibssa_opts.cfg		$conf_dir/DL_ibssa_opts.cfg
sudo cp $src_dir/distrib/ibssa_opts.cfg		$conf_dir/AL_ibssa_opts.cfg


sudo -E LD_LIBRARY_PATH=/usr/local/lib ib_acme -A -O -D $conf_dir/
if [ $install_type == "UPSTR" ]; then
	sudo LD_LIBRARY_PATH=/usr/local/lib /usr/local/sbin/opensm -c $conf_dir/opensm.conf
elif [ $install_type == "MOFED" ]; then
	# due to MOFED version of OpenSM that is installed into /usr and not /usr/local
	sudo LD_LIBRARY_PATH=/usr/lib /usr/sbin/opensm -c $conf_dir/opensm.conf
fi

sudo sed -i "s/event_plugin_name (null)/event_plugin_name opensmssa/g" $conf_dir/opensm.conf

sudo sed -i "s/^log_level 1/log_level 7/g" $conf_dir/ibssa_core_opts.cfg
sudo sed -i "s/^distrib_tree_level 0/distrib_tree_level 15/g" $conf_dir/ibssa_core_opts.cfg
sudo sed -i "s/^addr_preload 0/addr_preload 1/g" $conf_dir/ibssa_core_opts.cfg
sudo sed -i "s:^# addr_data_file /etc/rdma/ibssa_hosts.data:addr_data_file /etc/rdma/ibssa_hosts.data:g" $conf_dir/ibssa_core_opts.cfg
sudo sed -i "s/^log_level 1/log_level 7/g" $conf_dir/DL_ibssa_opts.cfg
sudo sed -i "s/^log_level 1/log_level 7/g" $conf_dir/AL_ibssa_opts.cfg
sudo sed -i "s/^log_level 1/log_level 7/g" $conf_dir/ibacm_opts.cfg
sudo sed -i "s/^neigh_mode 0/neigh_mode 3/g" $conf_dir/ibacm_opts.cfg
#sudo sed -i "s/^addr_preload none/addr_preload acm_hosts/g" $conf_dir/ibacm_opts.cfg
#sudo sed -i "s:^# addr_data_file /etc/rdma/ibacm_hosts.data:addr_data_file /etc/rdma/ibacm_hosts.data:g" $conf_dir/ibacm_opts.cfg

sudo sed -i "s/^node_type access/node_type distrib/g" $conf_dir/DL_ibssa_opts.cfg

sudo $WORKSPACE/ssa_tools/ssa_setup.sh load_modules

sudo rm -rf /var/cache/opensm

#TEMORARY SOLUTION TO DEAL WITH IPv6 user-space problems FIXME

sudo sed -i "s/^# support_ips_in_addr_cfg 0/support_ips_in_addr_cfg 1/g" $conf_dir/ibacm_opts.cfg
ipv6_line=`cat $conf_dir/ibacm_addr.data | tail -1`
part_to_replace=echo $ipv6_line | awk '{print $2}'
gid=`ibaddr | awk '{print $2}'`
ipv6_line=`echo $ipv6_line | sed "s/^$part_to_replace/$gid/"`
echo $ipv6_line >> $conf_dir/ibacm_addr.data

#END OF TEMPORARY SOLUTION

exit $status
