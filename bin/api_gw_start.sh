#!/bin/bash
  
echo "api_gw 시작"
nohup python3 -u ../src/api_gw.py &
echo "---------------------------------------------"
ps -ef | grep api_gw | grep -v grep
echo "---------------------------------------------"
