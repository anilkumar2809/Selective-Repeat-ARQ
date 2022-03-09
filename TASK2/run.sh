#!/bin/bash
 
# declare an array
arr=("100" "200" "700" "1000")
 
# for loop that iterates over each element in arr
for i in "${arr[@]}"
do
    python3 server.py Simple_ftp_server 7735 output.txt 0.05
    sleep 2
done