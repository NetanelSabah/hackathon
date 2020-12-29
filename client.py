import socket
import struct
import errno

import random
from logAndColor import *

import time

GROUP_NAME = "Hashawalilim"
MUL_CLIENT_TEST = True # for debugging multiple clients
UDP_PORT = 13117
MAGIC_COOKIE = 0xfeedbeef
TYPE = 0x2

message = ''

def nonBlockingReceive(sock, size): # will return data if received it, but will return None otherwise
    try:
        data = sock.recv(size)
        return data
    except socket.error as e:
        error_type = e.args[0]
        if (error_type == errno.EAGAIN or error_type == errno.EWOULDBLOCK):
            return None
        else:
            raise socket.error
    except Exception as e:
        raise e

# def nonBlockingInput


while True:
    try:
        # UDP connection setup
        UDPclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # set up UDP
        UDPclient.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # allow multiple clients (important)
        UDPclient.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # broadcast
    except Exception as e:
        print("couldn't connect to UDP connection, shutting down...")
        err("ERROR: " + str(e))
        break

    key_debug_count = random.randint(0, 10)

    #looking for a server
    print("Client started, listening for offer requests...")
    log("key debug count is %s" % (key_debug_count))
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
            continue
    
    # connecting to a server
    try:
        # setting up TCP socket
        TCPclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPclient.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
        TCPclient.connect((addr, port))

        # send first message (name)
        message = GROUP_NAME
        if (MUL_CLIENT_TEST):
            message += "_" + str(random.randint(0, 1000))
        TCPclient.send(bytes(message+"\n", 'utf-8'))

        # receive starting message from server
        message = TCPclient.recv(1048)
        print(message.decode('utf8'))
    except Exception as e:
        print("Couldn't connect via TCP to server at %s/%s."%(addr,port))
        err("ERROR: " + str(e))
        continue


    #game mode
    try:
        TCPclient.setblocking(0)  # set to non-blocking
        message = nonBlockingReceive(TCPclient, 1024)
        while message == None:
            if key_debug_count > 0:
                TCPclient.send(bytes('h', 'utf8'))
                key_debug_count -= 1
            time.sleep(0.001)
            message = nonBlockingReceive(TCPclient, 1024)
        print(message.decode('utf8'))

    except Exception as e:
        print("Encountered a problem via TCP connection to server at %s/%s." % (addr, port))
        err("ERROR: " + str(e))
        continue

    log("closing connection with %s/%s..." % (addr, port))
    TCPclient.close()

    #if (message == b''):  # close connection
    #    log("closing connection with %s/%s..." % (addr, port))
