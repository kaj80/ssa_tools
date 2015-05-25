#!/bin/bash

cd /tmp
zypper -n install -- readline-devel help2man git-email java-1_7_0-openjdk valgrind-devel
cd /tmp && git clone git://github.com/cgdb/cgdb.git && cd cgdb && ./autogen.sh && ./configure && make -j install
cp -p ~sashakot/bin/git-* ~/bin/


