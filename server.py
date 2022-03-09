import socket
import os
import threading
import struct
import sys
import random

BUFFER_SIZE = 4096
def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def checksum(msg):
    s = 0
    if len(msg)%2 == 1:
        msg+='0'
    #print(msg)
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def ack_connection(server_socket,FILENAME,P):
    file = open(FILENAME, "w")
    expected_sequence_number = 0
    file_received = False
    while file_received == False:
        (data_packet, client_address) = server_socket.recvfrom(BUFFER_SIZE)
        header = struct.unpack('!LHH', data_packet[0:8])
        data = str(data_packet[8:].decode())
        sequence_number = header[0]
        if header[2] != 0b0101010101010101 or checksum(data) != header[1]:
            print("Some ERROR Occured")
            continue
        if sequence_number <= expected_sequence_number:
            if random.random() > P:
                server_socket.sendto(struct.pack('!LHH', header[0], 0b0000000000000000, 0b1010101010101010), client_address)
                if len(data) > 0 and sequence_number == expected_sequence_number:
                    file.write(data)
                    expected_sequence_number+=1
                elif len(data)==0:
                    file.close()
                    server_socket.close()
                    file_received = True
            else:
                print("Packet loss, sequence number = "+str(sequence_number))
        #print("expected_sequence_number"+str(expected_sequence_number))

if __name__=="__main__":
    if len(sys.argv)!=5:
        """
        Command:
        Simple_ftp_server port# file-name p
        python3 server.py Simple_ftp_server 7735 output.txt 0.07
        """
        print("Please input correct command :- python3 server.py Simple_ftp_server 7735 output.txt 0.1")
        sys.exit()

    baseDir = "/Users/simstudent/Downloads/Project/PROJECT2/"
    FILENAME = str(sys.argv[3])
    if os.path.exists(baseDir +FILENAME):
        os.remove(baseDir +FILENAME)
    P = float(sys.argv[4])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', int(sys.argv[2])))
    print("UDP server up and listening")
    ack_thread = threading.Thread(target=ack_connection,args=(server_socket,baseDir +FILENAME,P))
    ack_thread.start()
    ack_thread.join()