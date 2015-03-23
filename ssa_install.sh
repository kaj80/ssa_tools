#!/bin/bash 

log=/tmp/install_$$.log

#check COVERAGE in environment
if [ -z $COVERAGE ];then
    COVERAGE=0
    INSTALL_LIBS="libibverbs librdmacm libibumad libmlx4 opensm ibssa2/plugin ibssa2/distrib ibssa2/acm"
else
    COVERAGE=1
    INSTALL_LIBS="opensm ibssa2/plugin ibssa2/distrib ibssa2/acm"
fi

echo $PATH

SCRIPT="`readlink -e $0`"
local_dir="`dirname $SCRIPT`"

export LD_LIBRARY_PATH=/usr/local/lib
export PATH=/usr/local:$PATH

function ssa_getsources {
    pushd /tmp
    git clone https://github.com/kaj80/ssa_upstream.git
    cd ssa_upstream/
    git submodule init
    git submodule update
    pushd $local_sources
    for lib in `ls`; do
        pushd $lib
        git checkout master 
        git pull
        popd
    done
    popd
}

if [ -z "$1" ] || [ "$1" == "-h" ]; then
    echo "Usage:"
    echo "      $0 <source_folder> <local_destination_folder>"
    echo "ex:   $0 /proj/SSA/Mellanox/sources /tmp/SSA"
   
fi

ARGC=$#
if [ $ARGC -lt 2 ]; then
    sources="`dirname $SCRIPT`/../sources"
    local_sources='/tmp/ssa_upstream'
    ssa_getsources
else
    sources=$1
    local_sources=$2
    \cp -r $sources $local_sources
    echo "cp -r $sources $local_sources"
fi

exec > >(tee $log)
exec 2>&1


export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH
mkdir -p $local_sources



function ssa_install {
    pushd $local_sources
    for lib in $INSTALL_LIBS
        do
            echo "*************************  INSTALL $lib ***********************************"
            config_opts=""
            pushd $local_sources/$lib
            make clean
            make mostlyclean
            make clean
            make distclean
            make maintainer-clean
            git status
            sync
            sleep 2

        if [ $COVERAGE -eq 1 ]; then 
            export PATH=/.autodirect/app/bullseye/bin/:$PATH
            export COVFILE=/tmp/`hostname`.cov
            cov01 -1
            echo "Started Coverage"
        else
            export PATH=/.autodirect/app/bullseye/bin/:$PATH
            cov01 -0
            echo "Stopped Coverage"
        fi

        ./autogen.sh && ./configure CFLAGS="-g -O0 -rdynamic" $config_opts &&  make all -j &&  make all install
        if [ $? -ne 0 ];then
            echo "Failed to install SSA $lib on `hostname`"
            exit 1
        fi
        popd
    done
    \cp $local_dir/etc/*.cfg /usr/local/etc/rdma/
    
}


ssa_install
exit 0
