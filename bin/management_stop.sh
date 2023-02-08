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

kill_proc user_management.py
kill_proc community_management.py
kill_proc system_management.py
kill_proc goods_management.py
kill_proc consignment_management.py
kill_proc move_management.py
kill_proc sale_management.py
kill_proc inventory_management.py
kill_proc revenue_management.py
kill_proc etc_management.py