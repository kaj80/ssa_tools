#!/bin/bash

install_dir=$1

if [ -z $install_dir ]; then
	echo "No install dir specified. Exiting ..."
	exit 1
fi

rm -rf $install_dir/bin/ib_acme
rm -rf $install_dir/etc/init.d/ibacm
rm -rf $install_dir/etc/init.d/ibssa
rm -rf $install_dir/lib/libopensmssa.*
rm -rf $install_dir/sbin/ibacm
rm -rf $install_dir/sbin/ibssa
rm -rf $install_dir/share/man/man1/ibacm.1
rm -rf $install_dir/share/man/man1/ib_acme.1
rm -rf $install_dir/share/man/man1/ibssa.1
rm -rf $install_dir/share/man/man7/ibacm.7
rm -rf $install_dir/share/man/man7/ibssa.7
rm -rf $install_dir/share/man/man7/opensmssa.7

echo "Finished uninstalling SSA."

