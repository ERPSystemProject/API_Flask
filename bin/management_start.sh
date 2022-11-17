#!/bin/bash
  
echo "user_management 시작"
nohup python3 -u ../src/user_management.py &
echo "---------------------------------------------"
ps -ef | grep user_management | grep -v grep
echo "---------------------------------------------"