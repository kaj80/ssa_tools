#!/bin/bash 


coverage_log=/tmp/static_code_check_$$.log
coverage_warnings_log=/tmp/warning_check_$$.log
log=/tmp/$0_$$.log
coverity_dir=/tmp/coverity_$$
cov_bin_dir=/.autodirect/sysgwork/coverity/cov-sa-linux64-5.5.1/bin

if [ "$1" == "-h" ];then
    echo "Run static code analazer"
    echo "$0 source_folder <default https://github.com/hnrose/ibssa2.git>"
    exit
fi
sources=$1

function get_code() {
    echo "*******************" >  $coverage_log
    if [ -z $sources ];then
        echo "Downloading from upstream" >> $coverage_log 
        mkdir $coverity_dir
        git clone https://github.com/hnrose/ibssa2.git $coverity_dir
    else
        echo "Checking in $sources" >> $coverage_log
        cp -r $sources $coverity_dir
    fi
    pushd $coverity_dir
    echo "This is static code analyze of the following code" >> $coverage_log
    git remote -v >> $coverage_log
    git log|head -n1 >> $coverage_log
    git status >> $coverage_log
    echo "*******************" >>  $coverage_log
    echo >>  $coverage_log
    echo >>  $coverage_log
    popd
}


function static {
    pushd $coverity_dir
    for lib in plugin distrib acm
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
            ${cov_bin_dir}/cov-format-errors --dir ${coverity_tmp_dir} --emacs-style 2>&1|tee >> $coverage_log
            popd
        done
    popd    
}


#exec > >(tee $log)
echo "Please, wait, while I am checking the SSA code for you."
echo "Hmmmm. Can you bring me something nice in the meanwhile :)"
#exec 1>>${log}
#exec 2>>${log}
#exec 2>&1

get_code $sources
static

echo "See test details in $log"
echo "See analize report in $coverage_log"
rm -rf $coverity_dir
exit 0

