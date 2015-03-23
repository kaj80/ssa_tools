#!/bin/bash

# Both PID and INTERVAL are intergers
declare -i PID INTERVAL

PID=$1
INTERVAL=$2
LOG_DIR=${3:-.}

# Make sure we got all the required arguments
if [[ -z $PID ]] || [[ $INTERVAL -eq 0 ]]; then
    echo "Usage: $(basename $0) <pid> <seconds>"
    exit
fi
# Redirect stdout to the log file
#exec 1>$LOG_DIR/server_counters_${PID}.csv

# Get the PID's process group
PGROUP=$(ps --no-header --pid=${PID} -o pgrp | xargs echo)

# Write the CSV header
echo "timestamp,rssize (private),vsize (virtual),%mem,%cpu,thread#,fd#"

# This function generates a single line of server counters
function print_output_line()
{
    # Put the output of ps in an array of comma sepereted values
    ps_data=( $(ps --no-headers -eLo "pgrp,rssize,vsize,%mem,%cpu" | grep "^ *$PGROUP " | sed 's/ * /,/g') )
    
    thread_count=${#ps_data[*]}
    fd_array=( /proc/$PID/fd/* )
    fd_count=${#fd_array[*]}

    # Sum the CPU usage of all the threads
    bc_input="0"
    for line in ${ps_data[*]} ; do
        line=( ${line//,/ } )
        bc_input="$bc_input + ${line[4]}"
    done
    cpu_usage=$(echo "$bc_input" | bc)

    # Write an output line 
    line=${ps_data[0]}
    line=( ${line//,/ } )
    echo $(date "+ +%b %d %H:%M:%S"),${line[1]},${line[2]},${line[3]},$cpu_usage,$thread_count,$fd_count
}

while [[ -d /proc/$PID ]] ; do
    print_output_line
    sleep $INTERVAL
done

exit 0
