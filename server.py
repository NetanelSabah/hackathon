import threading
import socket
import time
import struct

SERVER_UDP_PORT = 13117
SERVER_TCP_PORT = 5997
WAITING_FOR_CLIENT_COUNT = 5 # total time for the "waiting for client" mode
DEBUG = True

threads = []


def log(st):
    if DEBUG:
        print(bcolors.GREEN + st + bcolors.WHITE)

def err(st):
    if DEBUG:
        print(bcolors.RED + st + bcolors.WHITE)

class bcolors:
    RED = '\u001b[31m'
    GREEN = '\u001b[32m'
    YELLOW = '\u001b[33m'
    BLUE = '\u001b[34m'
    MAGENTA = '\u001b[35m'
    CYAN = '\u001b[36m'
    WHITE = '\u001b[37m'

class UDPBroadcast(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        

    def run(self):
        try:
            # UDP server setup
            UDPserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up UDP
            UDPserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
            UDPserver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #broadcast
            UDPserver.bind(('', SERVER_UDP_PORT))
            UDPserver.settimeout(0.2)

            # sending broadcast messages
            message = struct.pack('IBH', 0xfeedbeef, 0x2, SERVER_TCP_PORT)  # encode magic cookie, type and TCP port
            for i in range(WAITING_FOR_CLIENT_COUNT): #repeat 10 times
                UDPserver.sendto(message, ('<broadcast>', SERVER_UDP_PORT))
                log("%s) message sent!"%i)
                time.sleep(1) # wait a second between every broadcast
        except Exception as e:
                print("Failed to broadcast messages via UDP.\nERROR: "+str(e))
        log("UDP end")

class ClientThread(threading.Thread):
    def __init__(self, ip, port): 
        threading.Thread.__init__(self) 
        self.ip = ip 
        self.port = port
        log("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        while True:
            try:
                data = connectionSocket.recv(1048)
            except Exception as e:
                print("Client socket %s/%s failed.\n" %(ip, port))
                err("Error: "+str(e))
            print ("Server received data: %s"%data)
            #connectionSocket.send(b"message received")  # echo 
            if data == b'exit' or data ==  b'':
                print("closing connection...")
                break



try:
    #TCP server socket setup
    TCPserverIP = socket.gethostbyname(socket.gethostname()) #get the IP for printing the message
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('', SERVER_TCP_PORT))
    server.listen(1)
    print("Server started, listening on IP address %s for %s seconds"%(TCPserverIP,WAITING_FOR_CLIENT_COUNT))

    #UDP thread start
    UDPthread = UDPBroadcast()
    UDPthread.start()
    threads.append(UDPthread)

    #accept users in TCP
    initTime = time.time()
    remainingTime = WAITING_FOR_CLIENT_COUNT + 0.2 # initial remaining time, plus time to catch last requests from UDP broadcasts
    while remainingTime>0: 
        server.settimeout(remainingTime) # the timeout will be the remaining time
        (connectionSocket, (ip, port)) = server.accept()
        newThread = ClientThread(ip, port)
        newThread.start()
        threads.append(newThread)
        remainingTime = WAITING_FOR_CLIENT_COUNT-(time.time()-initTime) #set the remaining time to the server (essentially 10 - time elapsed since start)
except socket.timeout:
    pass
except Exception as e:
    print("TCP server socket failed.\n")
    err("Error: "+str(e))
print("Finished listening, game start...")


for t in threads:
    t.join()
      