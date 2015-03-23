#!/bin/bash 

log=/tmp/install_$$.log

COVERAGE="False"

SCRIPT="`readlink -e $0`"
local_dir="`dirname $SCRIPT`"
rm -f /var/lib/apt/lists/partial/repo.kodiak.nx_ubuntu_dists_precise_main_binary-amd64_Packages ; 
rm -f /var/lib/apt/lists/partial/repo.kodiak.nx_ubuntu_dists_precise-updates_main_binary-amd64_Packages
ifconfig ib0 down
function ssa_nome_twick {
	export http_proxy=http://ops:8888
        apt-get install pkg-config -y
        apt-get install zip pdsh -y
        rm -f /var/lib/apt/lists/partial/repo.kodiak.nx_ubuntu_dists_precise-updates_main_binary-amd64_Packages
        rm -f /var/lib/apt/lists/partial/repo.kodiak.nx_ubuntu_dists_precise_universe_binary-i386_Packages
	apt-get update
	dpkg --configure -a
	apt-get install  libglib2.0-0 libglib2.0-bin libglib2.0-data libglib2.0-dev libpackagekit-glib2-14 libpackagekit-glib2-dev libglib2.0-dev -y --force-yes
	cp /usr/share/aclocal/pkg.m4 /usr/local/share/aclocal/
}
ssa_nome_twick
exit 1

