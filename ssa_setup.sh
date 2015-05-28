#!/bin/bash

unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH
SRC_LIB="/mswg/projects/osm/kodiak/"

if [ -z "$SSA_DEST" ]; then
    SSA_DEST='.'
fi



function gnu_install {
        gnu_folder="/tmp/GNU_$$"
        pushd $gnu_folder
        tar -zxvf /mswg/projects/osm/kodiak/GNU.tgz
        pushd sources/
        for i in `ls` ; do pushd $i ; ./configure && make all && make all install ; popd; done
        popd
        rm -rf $gnu_folder
     	cp /usr/share/aclocal/pkg.m4 /usr/local/share/aclocal/pkg.m4
}


function imb_install {
    #install IMB
    pushd /tmp/ompi_release
    tar -zxvf /mswg/projects/osm/kodiak/imb.tgz
    pushd imb/src
    make -f make_mpich
    popd
    popd
}


function ompi_install {

    #rm -rf `locate openmpi`
    git clone https://github.com/mellanox-hpc/ompi-release /tmp/ompi_release
    pushd /tmp/ompi_release
    ./autogen.sh
    ./configure --enable-openib-rdmacm-ibaddr --enable-mpirun-prefix-by-default --with-verbs=/usr/local  --disable-openib-connectx-xrc
    make all
    make all install 2>&1|tee > /tmp/ompi_$$.log
    popd

}


function setup {
    rpm -e `rpm -qa | grep bfa-fir`
}


function kernel_install {
    src_lib=$SRC_LIB/kernel
    cd $src_lib
    rpm -ivh --force `ls `

    echo  "# current OS number 1" >> /boot/grub/menu.lst
    echo  "title RH6.4x64_AF" >> /boot/grub/menu.lst
    echo  "    root (hd0,0)" >> /boot/grub/menu.lst
    echo  "    kernel /vmlinuz-2.6.32-412.el6.x86_64 root=/dev/sda2 console=tty0 console=ttyS0,115200n8" >> /boot/grub/menu.lst
    echo  "       initrd /initramfs-2.6.32-412.el6.x86_64.img" >> /boot/grub/menu.lst
    perl -pi -e "s/default 0/default 1/g" /boot/grub/grub.conf
    mkdir /mnt/sda1
    mount /dev/sda1 /mnt/sda1
    cp $src_lib/sda/* /mnt/sda1
    cd /tmp
    tar -zxvf $src_lib/lib_modules.tgz 
    mv /tmp/lib/modules/* /lib/modules
    reboot
}

function install_env {
    rm -rf /etc/yum*
    cp -r $src_lib/yum* $src_lib/rc.modules /etc
    yum install infiniband-diags.x86_64 ibutils.x86_64 ibutils-libs.x86_64 make.x86_64 -y
    cp /usr/share/aclocal/pkg.m4 /usr/local/share/aclocal/pkg.m4

    pushd /tmp
    tar -zxvf $SRC_LIB/GNU.tgz
    cd sources
    for i in 'autoconf-2.69'  'automake-1.14.1'  'libtool-2.4.2'
    do
        echo "$PWD# ./configure make all make all install"
        pushd $i
        ./configure && make all  &&  make all install
        popd
    done
    popd

    echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/' >> ~/.bashrc
    echo 'export PATH=/usr/local:$PATH' >> ~/.bashrc
    source ~/.bashrc


    }


function load_modules {
    sudo /sbin/modprobe mlx4_ib
    sudo /sbin/modprobe ib_ipoib
    sudo /sbin/modprobe ib_umad
    sudo /sbin/modprobe rdma_ucm
    lsmod | grep ib
    #echo `hostname` > /sys/class/infiniband/mlx*/node_desc
}


function lib_download {
     if [[ -z "$SSA_LIBS_REPO" ]]; then
	SSA_LIBS_REPO="git://flatbed.openfabrics.org/~halr/opensm.git \
		       git://git.kernel.org/pub/scm/libs/infiniband/libibverbs.git \
		       git://git.kernel.org/pub/scm/libs/infiniband/libmlx4.git \
		       git://git.openfabrics.org/~shefty/librdmacm.git \
		       git://openfabrics.org/~halr/libibumad.git"
    fi
    pushd $SSA_DEST
    for git in $SSA_LIBS_REPO; do
        git clone $git
    done
}

function lib_install {
	if [ -z $OPTS ]; then
	    OPTS="--prefix=/usr"
	fi

        for lib in libibverbs libmlx4 librdmacm libibumad opensm
        do
            pushd $lib
	    grep -rl 'AC_PREREQ(\[2.67\]' . | xargs sed -i 's/AC_PREREQ(\[2.67\]/AC_PREREQ([2.63]/g'
	    ./autogen.sh && ./configure $OPTS && make all -j && sudo make all install
            if [ $? -ne 0 ];then
		echo "Failed to $cmd of $lib"
		popd
                exit 1
            fi
            popd
        done
}

RGV0=$0
ARGC=$#
if [ $ARGC == 0 ]; then
    echo "Export OPTS for lib configure options"
    echo "For ssa_install please set SSA_DEST=<destination folder>"
    echo "Usage:"
    echo "      $0 <setup|kernel_install|lib_install|lib_download|load_modules|ssa_install|install_env|ompi_install|imb_install>"

    exit 1
fi 

i=1
while [ $i -le $ARGC ]; do
    echo "Executing:  ${!i}"
    ${!i}
    i=$((i+1))
done


