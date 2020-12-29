import threading
import socket
import time
import struct
import random
from logAndColor import *

SERVER_UDP_PORT = 13117
SERVER_TCP_PORT = 5997
WAITING_FOR_CLIENT_COUNT = 15 # total time for the "waiting for client" mode
WAITING_FOR_CLIENT_EXTRA = 0.2 # additional time to catch last requests
UDP_TIMEOUT = 0.2 #timeout for UDP server
MAGIC_COOKIE = 0xfeedbeef #UDP header cookie
TYPE = 0x2 # UDP messagetype

threads = [] # TCP client threads pool
player_sockets = {} # player sockets pool (dictionary of format name:{socket : <value>, thread : <value>, status : <value>})
player_sockets_grouping_list = []
player_sockets_lock = threading.Lock()
start_game_event = threading.Event()
message_lock = threading.Lock()

group1 = []
group2 = []

message = ''

# UDP thread
class UDPBroadcast(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        

    def run(self):
        try:
            # UDP server setup
            UDP_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up UDP
            UDP_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
            UDP_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #broadcast
            UDP_server.bind(('', SERVER_UDP_PORT))
            UDP_server.settimeout(UDP_TIMEOUT)

            # sending broadcast messages
            message = struct.pack('IBH', MAGIC_COOKIE, TYPE, SERVER_TCP_PORT)  # encode magic cookie, type and TCP port
            for i in range(WAITING_FOR_CLIENT_COUNT): #repeat 10 times
                UDP_server.sendto(message, ('<broadcast>', SERVER_UDP_PORT))
                log("%s) message sent!"%i)
                time.sleep(1) # wait a second between every broadcast
        except Exception as e:
            print("Failed to broadcast messages via UDP.\nERROR: "+str(e))
        log("UDP end")



# client thread
class ClientThread(threading.Thread):
    def __init__(self, client_ip, client_port, client_socket):
        threading.Thread.__init__(self)
        self.client_ip = client_ip
        self.client_port = client_port
        self.client_socket = client_socket
        self.name = ''
        log("New server socket thread started for " + self.client_ip + ":" + str(self.client_port))

    def run(self):
        acquired = False
        try:
            data = self.client_socket.recv(1048)
            result = data.decode('utf8')
            result_length = len(result)
            if (result_length > 0 and result[-1] == '\n'): # check if it's a name
                name = result[:-1]
                if (player_sockets.get(name) == None):
                    log("player added to pool: %s" % name)
                    player_sockets[name] = {'connection' : self.client_socket, 'thread': threading.get_ident(), 'status' : True}
                else:
                    print("group with that name already exists, closing connection.")
                    self.client_socket.close()
                    return
            else:
                print("got an invalid connection message (does not end with newline), closing connection.")
                self.client_socket.close()
                return

            # wait until game start
            start_game_event.wait()

            while (not message_lock.acquire()):
                start_game_event.wait()
            acquired = True # lock has been acquired, used to release it incase of failure of sending the following file

            self.client_socket.send(bytes(message, 'utf-8'))
            log("sent game start message %s to %s/%s" % (message[:15], self.client_ip, self.client_port))

            message_lock.release()
            start_game_event.set()

        except Exception as e:
            print("Client socket %s/%s failed." %(self.client_ip, self.client_port))
            err("Error: "+str(e))
            if (acquired):
                message_lock.release()
                start_game_event.set()
        log("closing connection with %s/%s..." %(self.client_ip, self.client_port))
        if (player_sockets.get(name) != None):
            player_sockets[name]['status'] = False
        self.client_socket.close()


try:
    #TCP server socket setup
    TCP_server_IP = socket.gethostbyname(socket.gethostname()) #get the IP for printing the message
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('', SERVER_TCP_PORT))
    server.listen(1)
    print("Server started, listening on IP address %s for %s seconds"%(TCP_server_IP,WAITING_FOR_CLIENT_COUNT))

    # UDP thread start
    UDP_thread = UDPBroadcast()
    UDP_thread.start()
    
    # accept users in TCP
    initTime = time.time()
    remainingTime = WAITING_FOR_CLIENT_COUNT + WAITING_FOR_CLIENT_EXTRA # initial remaining time, plus time to catch last requests from UDP broadcasts
    while remainingTime>0: 
        server.settimeout(remainingTime) # the timeout will be the remaining time
        (connectionSocket, (ip, port)) = server.accept()
        new_thread = ClientThread(ip, port, connectionSocket)
        new_thread.start()
        threads.append(new_thread)
        remainingTime = WAITING_FOR_CLIENT_COUNT-(time.time()-initTime) #set the remaining time to the server (essentially 10 - time elapsed since start)
except socket.timeout:
    pass # timeouts are OK.
except Exception as e:
    print("TCP server socket failed.")
    err("Error: "+str(e))
log("Finished listening, game start...")

# shuffling the clients randomly

player_sockets_grouping_list = list(player_sockets.keys())
random.shuffle(player_sockets_grouping_list)

# now, the teams will be assigned in the following order: even - group 1, odd - group 2
group1 = player_sockets_grouping_list[::2]
group2 = player_sockets_grouping_list[1::2]

log("shuffled teams...")

# set message to start
message = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n%s\nGroup 2:\n==\n%s\nStart pressing keys on your keyboard as fast as you can!!" % ('\n'.join(group1), '\n'.join(group2)) # the start message
# wake client threads
start_game_event.set() # wake all client threads to make them send the message


for t in threads:
    t.join()
UDP_thread.join()