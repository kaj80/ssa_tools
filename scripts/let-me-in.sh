#!/bin/sh

echo "in a new computer use \"ssh-keygen -t dsa\" before let_me_in"
if [ $# != 1 ]; then
echo "Usage:  $0 hostname"
exit 1
fi
cat ~/.ssh/id_dsa.pub | ssh -o "ConnectTimeout=1" $1  "cat >> ~/.ssh/authorized_keys"

