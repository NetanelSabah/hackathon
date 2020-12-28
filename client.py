import socket
import struct
from logAndColor import *

import time

GROUP_NAME = "Hashawalilim"
UDP_PORT = 13118
MAGIC_COOKIE = 0xfeedbeef
TYPE = 0x2

while True:
    #UDP connection setup
    UDPclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up UDP
    UDPclient.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
    UDPclient.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #broadcast

    #looking for a server
    print("Client started, listening for offer requests...")
    serverLookup = True
    UDPclient.bind(("", UDP_PORT))
    while serverLookup:
        data, (addr, port) = UDPclient.recvfrom(1024)
        log("received data %s from IP %s."%(data,addr))
        try:
            (cookie,typ,port) = struct.unpack('IBH', data)
            if (cookie == MAGIC_COOKIE and typ == TYPE):
                UDPclient.close()
                log("UDP end")
                print("Received offer from %s, attempting to connect..."%addr)
                serverLookup = False
            else:
                print("Received incoming message, but it was not a proper UDP server message (wrong cookie/type).")
        except Exception as e:
            print("Received incoming message, but couldn't decode the data")
            err("ERROR: " + str(e))
    
    #connecting to a server
    try:
        #setting up TCP socket
        TCPclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        TCPclient.connect((addr, port))
        
        TCPclient.send(bytes(GROUP_NAME+"\n", 'utf-8'))
        time.sleep(15)
        TCPclient.close()


    except Exception as e:
        print("Couldn't connect via TCP to server at %s/%s."%(addr,port))
        err("ERROR: "+ str(e))