#!/bin/bash
 
# declare an array
arr=("100" "200" "700" "1000")

# for loop that iterates over each element in arr
for i in "${arr[@]}"
do
    python3 client.py Simple_ftp_server 127.0.0.1 7735 abc.txt 64 $i
    sleep 5
done