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

echo "consignment_management 시작"
nohup python3 -u ../src/consignment_management.py &
echo "---------------------------------------------"
ps -ef | grep consignment_management | grep -v grep
echo "---------------------------------------------"

echo "move_management 시작"
nohup python3 -u ../src/move_management.py &
echo "---------------------------------------------"
ps -ef | grep move_management | grep -v grep
echo "---------------------------------------------"

echo "sale_management 시작"
nohup python3 -u ../src/sale_management.py &
echo "---------------------------------------------"
ps -ef | grep sale_management | grep -v grep
echo "---------------------------------------------"

echo "inventory_management 시작"
nohup python3 -u ../src/inventory_management.py &
echo "---------------------------------------------"
ps -ef | grep inventory_management | grep -v grep
echo "---------------------------------------------"

echo "revenue_management 시작"
nohup python3 -u ../src/revenue_management.py &
echo "---------------------------------------------"
ps -ef | grep revenue_management | grep -v grep
echo "---------------------------------------------"

echo "etc_management 시작"
nohup python3 -u ../src/etc_management.py &
echo "---------------------------------------------"
ps -ef | grep etc_management | grep -v grep
echo "---------------------------------------------"
