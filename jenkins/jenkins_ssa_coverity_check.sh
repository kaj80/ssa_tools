#!/bin/bash 

function static {
    cov_bin_dir=/.autodirect/sysgwork/coverity/cov-sa-linux64-5.5.1/bin
    coverity_dir=$1
    pushd $coverity_dir
    echo "*************************  Checking SSA ***********************************"
    module="SSA"
    ./autogen.sh
    ./configure
    ${cov_bin_dir}/cov-build --dir .  make -j
    ${cov_bin_dir}/cov-analyze --dir .
    #${cov_bin_dir}/cov-format-errors --dir ${coverity_tmp_dir} --emacs-style 2>&1|tee > coverity_SSA.log
    ${cov_bin_dir}/cov-format-errors --dir .  2>&1|tee > coverity_SSA.log
    echo "FINISHED Checking $coverity_dir/coverity_SSA.log ***********************************"
    popd
}


if [ "$#" -ne 1 ];then
    echo "$0 <source path>"
    exit 1
fi


exec > >(tee $log)
exec 2>&1

static $1
exit 0

