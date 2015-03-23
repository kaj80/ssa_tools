#!/bin/bash

DLID=`/usr/sbin/ibstat |grep SM|awk '{print $3}'`
SLID=`/usr/sbin/ibstat |grep Base|awk '{print $3}'`
if [ -z $1 ]; then
	delay=3
else
	delay=$1
fi
while [ 1 ] 
do 
	sleep $delay
	date=`date`
	echo "$date /usr/local/bin/ib_acme -f l -d $DLID -c -v -s $SLID; sleep $delay"
	/usr/local/bin/ib_acme -f l -d $DLID -c -v -s $SLID
done
