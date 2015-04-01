#!/bin/bash
export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH
export PATH=/usr/local/bin/:/usr/local/sbin/:/usr/sbin/:/usr/bin/:$PATH

STATUS_FILE=rsocket.test.status

if [[ $# > 0 ]];then
	REMOTE=$1;
	pdsh -w $REMOTE 'uname -mrs'
	pdsh -w $REMOTE 'cat /etc/*release | head -n1'
else
	echo "ERROR: There is no remote server name"
	echo "Usage: test_rsocket <remote server name>"
	exit 1
fi

if [[ -z $REMOTE ]]; then
	exit 1;
fi

which pdsh > /dev/null 2>&1
rc=$?
if [[ $rc != 0 ]]; then
	echo "ERROR: pdsh not found"
	exit $rc
fi

ibaddr > /dev/null
rc=$?
if [[ $rc != 0 ]]; then
	echo "ERROR: ibaddr failed"
	exit $rc
fi

sminfo > /dev/null 2>&1
rc=$?
if [[ $rc != 0 ]]; then
	opensm -B
fi

GID=`ibaddr | awk '{print $2}'`
echo "Server GID: $GID"

status=0

for tool in rstream riostream; do
	for blocking in b n; do
		for async in a none; do
			TEST_CMD="$tool -f gid"
			TEST_CMD+=" -T $blocking"

			if [ $tool == "rstream" ]; then
				TEST_CMD+=" -k 30 "
			fi

			if [ $async == "a" ]; then
				TEST_CMD+=" -T a "
			fi

			echo "Test: $TEST_CMD"
			pkill -9 -f "$GID" > /dev/null 2>&1

			rm -f "$STATUS_FILE"

			($TEST_CMD -b "$GID" > /dev/null; echo "result: $?" >  $STATUS_FILE)&
			SERVER_PID=$!
			echo "pid: $SERVER_PID" > $STATUS_FILE 
			kill -0 $SERVER_PID 2>/dev/null
			rc=$?
			if [[ $rc != 0 ]]; then
				echo "ERROR: Server is not running. $TEST_CMD"
				let status=status+rc
				break
			fi

			echo "Server pid: $SERVER_PID"

			REMOTE_COMMAND='export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH; export PATH=/usr/local/bin:$PATH;'
			REMOTE_COMMAND+=" $TEST_CMD -s $GID"
			echo $REMOTE_COMMAND
			pdsh -t 20 -w $REMOTE pkill -9 -f $GID
			pdsh -t 20 -u 60 -w $REMOTE $REMOTE_COMMAND
			rc=$?
			pdsh -t 20 -w $REMOTE pkill -9 -f $GID
			if [[ $rc != 0 ]]; then
				echo "ERROR: Test failed. $TEST_CMD";
				let status=status+rc
				pkill -9 -f "$GID" > /dev/null 2>&1
				rm -f $STATUS_FILE > /dev/null 2>&1
				break
			fi

			kill -0 $SERVER_PID 2>/dev/null
			rc=$?
			if [[ $rc -eq 0 ]]; then
				echo "ERROR: Server is running after test. $TEST_CMD"
				let status=status+1
				pkill -9 -f "$GID" > /dev/null 2>&1
				rm -f $STATUS_FILE > /dev/null 2>&1
				break
			fi

			server_ret_val="$(grep "result" $STATUS_FILE | awk '{print $2}')"
			if [[ $server_ret_val != "0" ]]; then
				echo "ERROR: Server error: $server_ret_val . $TEST_CMD"
				let status=status+1
				pkill -9 -f "$GID" > /dev/null 2>&1
				rm -f $STATUS_FILE > /dev/null 2>&1
				break

			fi

			rm -f $STATUS_FILE > /dev/null 2>&1

		done
	done
done

rm -f $STATUS_FILE > /dev/null 2>&1
exit $status
