#!/bin/bash

str="g_al_callback"

thread_cnt=(`cat /var/log/ibssa.log | egrep "$str" | cut -d" " -f5 | sort | uniq -c | rev | cut -d" " -f2 | rev`)
thread_ids=(`cat /var/log/ibssa.log | egrep "$str" | cut -d" " -f5 | sort | uniq -c | rev | cut -d" " -f1 | rev | cut -c2-9`)


for (( i=0; i < ${#thread_ids[@]}; i++ ))
do
    printf "$str: thread ID %-10s jobs %-10s\n" "${thread_ids[$i]}" "${thread_cnt[$i]}"
done

