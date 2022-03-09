#!/bin/bash
 
# declare an array
arr=("0.01" "0.03" "0.1")

# for loop that iterates over each element in arr
for i in "${arr[@]}"
do
    python3 client.py Simple_ftp_server 127.0.0.1 7735 abc.txt 64 500
    sleep 5
done