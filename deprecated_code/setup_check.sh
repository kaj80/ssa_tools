#!/bin/bash


date=`date`
ibssa_version=`ibssa -v|awk '{print $NF}'`
ibacm_version=`ibacm -v|awk '{print $NF}'`
opensm_version=`opensm --version|grep Op|awk '{print $NF}'`
kernel_pattern=`cat /etc/sysctl.conf |grep core_pattern`
free_storage=`df -lh |egrep '/$'|awk '{print $5}'`
ib_stat=`ibstat |grep Act|awk '{print $NF}'`
linux=`uname -a`

echo `hostname` > /sys/class/infiniband/mlx4_0/node_desc




