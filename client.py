import sys
import socket
import struct
import threading
import time

def ack_function():
    global SERVER_HOSTNAME,SERVER_PORT,FILENAME,WINDOW_SIZE,MSS,TIMEOUT_TIME,DATA_BUFFER_SIZE,current_window_data,transmission_lock,client_socket,file_read
    while True:
        if file_read and not current_window_data:
            break
        (ack, server_address) = client_socket.recvfrom(DATA_BUFFER_SIZE)
        header = struct.unpack('!LHH', ack[0:8])
        if header[1] != 0b0000000000000000:
            print("Some ERROR Occured")
            continue
        if header[2] != 0b1010101010101010:
            print("Some ERROR Occured")
            continue
        sequence_number = header[0]
        transmission_lock.acquire()
        cumulativeACK = True
        if cumulativeACK == True:
            for i in range(len(current_window_data)):
                if current_window_data[i][0] == sequence_number:
                    current_window_data = current_window_data[i+1:]
                    break
        elif cumulativeACK ==False:
            if len(current_window_data)>0 and current_window_data[0][0] == sequence_number:
                current_window_data = current_window_data[1:]
        transmission_lock.release()

def transmit_function():
    global SERVER_HOSTNAME,SERVER_PORT,FILENAME,WINDOW_SIZE,MSS,TIMEOUT_TIME,DATA_BUFFER_SIZE,current_window_data,transmission_lock,client_socket,file_read
    file = open(FILENAME, "r")
    sequence_number = 0
    while True:
        while len(current_window_data) >= WINDOW_SIZE:
            time.sleep(0.1)
        #print("sequence_number"+str(sequence_number))
        if file_read == True:
            header = struct.pack('!LHH', sequence_number, checksum(''), 0b0101010101010101)
            transmission_lock.acquire()
            current_window_data.append([sequence_number,header,time.time()])
            transmission_lock.release() 
            client_socket.sendto(header, (SERVER_HOSTNAME, SERVER_PORT))
            break
        data_read = ''
        while MSS >len(data_read):
            input_data_byte = file.read(1)
            if not input_data_byte:
                file_read = True
                file.close()
                break
            data_read = data_read + input_data_byte
        if len(data_read)>0:
            header = struct.pack('!LHH', sequence_number,   checksum(data_read), 0b0101010101010101)
            packet_to_transfer = header+str(data_read).encode()
            transmission_lock.acquire()
            current_window_data.append([sequence_number,packet_to_transfer,time.time()])
            transmission_lock.release()
            client_socket.sendto(packet_to_transfer, (SERVER_HOSTNAME, SERVER_PORT))
            sequence_number=sequence_number+1

def checkTimeout():
    global SERVER_HOSTNAME,SERVER_PORT,FILENAME,WINDOW_SIZE,MSS,TIMEOUT_TIME,DATA_BUFFER_SIZE,current_window_data,transmission_lock,client_socket,file_read
    if len(current_window_data)>0:
        return (time.time() - current_window_data[0][2]) > TIMEOUT_TIME
    return False

def retransmit_packet():
    global SERVER_HOSTNAME,SERVER_PORT,FILENAME,WINDOW_SIZE,MSS,TIMEOUT_TIME,DATA_BUFFER_SIZE,current_window_data,transmission_lock,client_socket,file_read
    transmission_lock.acquire()
    for i in range(len(current_window_data)):
        current_window_data[i][2] = time.time()
        client_socket.sendto(current_window_data[i][1], (SERVER_HOSTNAME, SERVER_PORT))
    transmission_lock.release()


def retransmit_function(transmit_thread,ack_thread):
    global SERVER_HOSTNAME,SERVER_PORT,FILENAME,WINDOW_SIZE,MSS,TIMEOUT_TIME,DATA_BUFFER_SIZE,current_window_data,transmission_lock,client_socket,file_read
    while True:
        if transmit_thread.is_alive():
            time.sleep(TIMEOUT_TIME)
            if checkTimeout():
                print("Timeout occured for sequence number = " +str(current_window_data[0][0])+" Retransmittting it now")
                retransmit_packet()
        elif ack_thread.is_alive():
            time.sleep(TIMEOUT_TIME)
            if checkTimeout():
                print("Timeout occured for sequence number = " +str(current_window_data[0][0])+" Retransmittting it now")
                retransmit_packet()
        elif not transmit_thread.is_alive() and not ack_thread.is_alive():
            break

#Referance for checksum :- https://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
#https://github.com/houluy/UDP/blob/master/udp.py
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


if __name__=="__main__":
    if len(sys.argv)!=7:
        """
        Command:
        Simple_ftp_server server-host-name server-port file-name N MSS
        """
        print("Please input correct command :- python3 client.py Simple_ftp_server server-host-name server-port input-file-name N MSS")
        sys.exit()

    global SERVER_HOSTNAME,SERVER_PORT,FILENAME,WINDOW_SIZE,MSS,TIMEOUT_TIME,DATA_BUFFER_SIZE,current_window_data,transmission_lock,client_socket,file_read

    SERVER_HOSTNAME = sys.argv[2]
    SERVER_PORT = int(sys.argv[3])
    FILENAME = str(sys.argv[4])
    WINDOW_SIZE = int(sys.argv[5])
    MSS = int(sys.argv[6])
    TIMEOUT_TIME = 1
    DATA_BUFFER_SIZE = 4096
    current_window_data = []
    transmission_lock = threading.RLock()
    file_read = False
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    transmit_thread = threading.Thread(target=transmit_function)
    ack_thread = threading.Thread(target=ack_function)
    retransmit_thread = threading.Thread(target=retransmit_function,args=(transmit_thread,ack_thread,))
  
    start_time = time.time()
    ack_thread.start()
    transmit_thread.start()
    retransmit_thread.start()
  
    retransmit_thread.join()
    transmit_thread.join()
    ack_thread.join()

    print("Total time taken to transfer data: ", time.time()-start_time)
    client_socket.close()