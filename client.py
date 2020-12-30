import socket
import struct
import errno

import sys
import termios
import tty
import select

import random
from logAndColor import *

import time

GROUP_NAME = "Hashawalilim"
MUL_CLIENT_TEST = False # for debugging multiple clients
UDP_PORT = 13117
MAGIC_COOKIE = 0xfeedbeef
TYPE = 0x2
CYCLE_WAIT = 2  # num of seconds to wait before restarting the

if (MUL_CLIENT_TEST):
            GROUP_NAME += "_" + str(random.randint(0, 1000))

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

class nonBlockingInput():
    def __init__(self):
        self.toggle = False # non blocking getch will only work if the toggle is true
        self.old_config = termios.tcgetattr(sys.stdin) # save the old settings

    def toggleOn(self):
        self.toggle = True
        tty.setcbreak(sys.stdin.fileno())
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)

    def toggleOff(self):
        self.toggle = False
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_config)

    def nonBlockingGetch(self):
        if not self.toggle:
            raise Exception("attempted to call non-blocking getch when the toggle is off")
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        else:
            return None

nbi = nonBlockingInput()  # will be used during the game to get characters

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

    #looking for a server
    print("Client started, listening for offer requests...")
    serverLookup = True
    UDPclient.bind(("", UDP_PORT))
    while serverLookup:
        data, (addr, port) = UDPclient.recvfrom(1024)
        log("received data %s from IP %s."%(data,addr))
        try:
            (cookie,typ,port) = struct.unpack('IbH', data)
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
        TCPclient.connect((addr, port))

        # send first message (name)
        message = GROUP_NAME
        TCPclient.send(bytes(message+"\n", 'utf-8'))

        # receive starting message from server
        message = TCPclient.recv(1048)
        print(message.decode('utf8'))
        if message == b'':
            print("Connection with server lost.")
            log("closing connection with %s/%s..." % (addr, port))
            TCPclient.close()
            continue
    except Exception as e:
        print("Couldn't connect via TCP to server at %s/%s."%(addr,port))
        err("ERROR: " + str(e))
        log("closing connection with %s/%s..." % (addr, port))
        TCPclient.close()
        continue


    #game mode
    try:
        TCPclient.setblocking(0)  # set to non-blocking
        message = nonBlockingReceive(TCPclient, 1024)
        nbi.toggleOn()
        while message == None:
            char = nbi.nonBlockingGetch()
            if char != None:
                TCPclient.send(bytes(char, 'utf8'))
            message = nonBlockingReceive(TCPclient, 1024)
            time.sleep(0.001)
        nbi.toggleOff()
        if message == b'':
            print("Connection with server lost.")
        else:
            print(message.decode('utf8'))

    except Exception as e:
        print("Encountered a problem via TCP connection to server at %s/%s." % (addr, port))
        err("ERROR: " + str(e))
        nbi.toggleOff()
        log("closing connection with %s/%s..." % (addr, port))
        TCPclient.close()
        continue

    log("closing connection with %s/%s..." % (addr, port))
    TCPclient.close()

    #if (message == b''):  # close connection
    #    log("closing connection with %s/%s..." % (addr, port))
