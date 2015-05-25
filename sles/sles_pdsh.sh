#!/bin/bash

for server in "$@"; do
	echo $server
#	ssh $server "rm -f ~/.ssh/authorized_keys"
	ssh-copy-id -i $server
	ssh $server "cd /tmp && wget --no-check-certificate  https://pdsh.googlecode.com/files/pdsh-2.29.tar.bz2 && tar xvf pdsh-2.29.tar.bz2"
	ssh $server "cd /tmp/pdsh-2.29  && ./configure --with-ssh && make -j install"
	ssh $server 'echo  "export PDSH_RCMD_TYPE=ssh" >> ~/.bashrc'
	ssh $server "systemctl restart autofs"
done
