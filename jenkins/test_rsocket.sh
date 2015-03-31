#!/bin/bash
export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH

if [[ $# > 0 ]];then
	REMOTE=$1;
	echo "Remote server: $REMOTE"
else
	echo "ERROR: There is no remote server name"
	echo "Usage: test_rsocket <remote server name>"
	exit 1
fi

if [[ -z $REMOTE ]]; then
	exit 1;
fi

for tool in rstream riostream; do
	TEST_CMD="$tool -f gid"

	if [ $tool = "rstream"]; then
		TEST_CMD+=" -k 30 "
	fi

	echo "Test: $TEST_CMD"

	ibaddr > /dev/null
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "ERROR: ibaddr failed"
		exit $rc
	fi 

	GID=`ibaddr | awk '{print $2}'`
	echo "Server GID: $GID"

	pkill -9 $tool

	$TEST_CMD -b "$GID" > log.txt &
	SERVER_PID=$!
	kill -0 $SERVER_PID 2>/dev/null
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "ERROR: Server is not running. $TEST_CMD"
		exit $rc
	fi

	echo "Server pid: $SERVER_PID"

	REMOTE_COMMAND='export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH; export PATH=/usr/local/bin:$PATH;'
	REMOTE_COMMAND+=" $TEST_CMD -s $GID" 
	echo $REMOTE_COMMAND
	pdsh -w $REMOTE "'pkill -9 $tool' > /dev/null 2>&1"
	pdsh -u 10 -w $REMOTE $REMOTE_COMMAND
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "ERROR: Test failed. $TEST_CMD";
	fi

	kill -0 $SERVER_PID 2>/dev/null
	rc=$?
	if [[ $rc -eq 0 ]]; then
		echo "ERROR: Server is running after test. $TEST_CMD"
		exit 1
	fi

	pkill -9 $tool

	done


exit 0
