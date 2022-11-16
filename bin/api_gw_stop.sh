#!/bin/bash
  
function kill_proc()
{
        echo "$1 중지 ...."
        pids=$(ps -ef | grep $1 | grep python | awk -F " " '{print $2}');
        if [ "$pids" = "" ]
        then
                echo "..... $1 .이미 중지되었다 ...."
        else
                echo "...... $1 PID [${pids}] ...."
                kill $pids
        fi
        pids=$(ps -ef | grep $1 | grep python | awk -F " " '{print $2}');
}

echo ""

kill_proc api_gw.py