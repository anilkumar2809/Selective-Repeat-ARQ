#!/bin/bash
 
# declare an array
arr=("0.01" "0.03"  "0.1")
 
# for loop that iterates over each element in arr
for i in "${arr[@]}"
do
    python3 server.py Simple_ftp_server 7735 output.txt $i
    sleep 2
done