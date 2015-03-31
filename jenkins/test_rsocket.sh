#!/bin/bash

TEST="rstream -f gid"

if [[ $# > 0 ]]; then REMOTE=$1; fi
if [[ -z $REMOTE ]]; then exit 1; fi

echo "Remote server: $REMOTE"
echo "Test: $TEST"

ibaddr > /dev/null
rc=$?;if [[ $rc != 0 ]]; then exit $rc; fi 

GID=`ibaddr | awk '{print $2}'`
echo "Server GID: $GID"

pkill -9 $TEST

$TEST -b $GID &
SERVER_PID=$!
kill -0 $SERVER_PID 2 >/dev/null
rc=$?;if [[ $rc != 0 ]]; then exit $rc; fi
echo "$SERVER_PID"

REMOTE_COMMAND="pkill -9 $TEST; $TEST -s $GID"
echo $REMOTE_COMMAND

pdsh -w $REMOTE "pkill -9 $TEST"
pdsh -u 10 -N -w "$REMOTE" "$REMOTE_COMMAND"
rc=$?;if [[ $rc != 0 ]]; then echo "Test failed"; fi

kill -9 $SERVER_PID

exit $rc
