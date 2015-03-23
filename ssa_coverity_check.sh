#!/bin/bash 

log=/tmp/install_$$.log



function static {
    cov_bin_dir=/.autodirect/sysgwork/coverity/cov-sa-linux64-5.5.1/bin
    coverity_dir=/tmp/coverity_$$
    mkdir $coverity_dir
    pushd $coverity_dir
    git clone https://github.com/hnrose/ibssa2.git
    for lib in ibssa2/plugin ibssa2/distrib ibssa2/acm
        do
            echo "*************************  Checking $lib ***********************************"
            pushd $lib
            module=`basename $lib`
            coverity_tmp_dir=`pwd`
            make clean
            make mostlyclean
            make clean
            make distclean
            make maintainer-clean
            git status
            sync
            sleep 2
            ./autogen.sh 
            ./configure
            ${cov_bin_dir}/cov-build --dir ${coverity_tmp_dir} make -j4
            ${cov_bin_dir}/cov-analyze --dir ${coverity_tmp_dir} 
            ${cov_bin_dir}/cov-format-errors --dir ${coverity_tmp_dir} --emacs-style 2>&1|tee > coverity_$module.log
            echo "FINISHED Checking $coverity_dir/$lib/coverity_$module.log ***********************************"
            popd
        done
    popd    
}

function dynamic {
    mkdir /tmp/ssa_upstream
    pushd /tmp/ssa_upstream
    git clone https://github.com/hnrose/ibssa2.git
    export PATH=/.autodirect/app/bullseye/bin/:$PATH
    export COVFILE=/tmp/`hostname`.cov
    cov01 -1

    for lib in ibssa2/plugin ibssa2/distrib ibssa2/acm
        do
            echo "*************************  Checking $lib ***********************************"
            pushd $lib
            module=`basename $lib`
            make clean
            make mostlyclean
            make clean
            make distclean
            make maintainer-clean
            git status
            sync
            sleep 2
            ./autogen.sh && ./configure && make all && make all install
            popd
        done
    popd    
}


if [ -e $1 ];then
    echo "$0 <dynamic|static>"
    exit 1
fi


exec > >(tee $log)
exec 2>&1

$1
exit 0

