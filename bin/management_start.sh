#!/bin/bash
  
echo "user_management 시작"
nohup python3 -u ../src/user_management.py &
echo "---------------------------------------------"
ps -ef | grep user_management | grep -v grep
echo "---------------------------------------------"

echo "community_management 시작"
nohup python3 -u ../src/community_management.py &
echo "---------------------------------------------"
ps -ef | grep community_management | grep -v grep
echo "---------------------------------------------"

echo "system_management 시작"
nohup python3 -u ../src/system_management.py &
echo "---------------------------------------------"
ps -ef | grep system_management | grep -v grep
echo "---------------------------------------------"

echo "goods_management 시작"
nohup python3 -u ../src/goods_management.py &
echo "---------------------------------------------"
ps -ef | grep goods_management | grep -v grep
echo "---------------------------------------------"

echo "etc_management 시작"
nohup python3 -u ../src/etc_management.py &
echo "---------------------------------------------"
ps -ef | grep etc_management | grep -v grep
echo "---------------------------------------------"
