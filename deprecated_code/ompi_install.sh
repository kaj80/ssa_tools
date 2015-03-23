#~/bin/bash

cd /tmp
tar -zxvf /mswg/projects/osm/kodiak/GNU.tgz
pushd sources/
for i in `ls` ; do pushd $i ; ./configure && make all && make all install ; popd; done
popd
rm -rf /tmp/sources
export PATH=/usr/local/bin:$PATH
rm -rf `locate openmpi`
git clone https://github.com/mellanox-hpc/ompi-release /tmp/ompi_release
cd /tmp/ompi_release
./autogen.sh && ./configure --enable-openib-rdmacm-ibaddr --enable-mpirun-prefix-by-default --with-verbs=/usr/local  --disable-openib-connectx-xrc &&  make all && make all install 2>&1|tee > /tmp/ompi_$$.log
make all install 2>&1|tee>/dev/null
exit $?

