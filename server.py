import threading
import socket
import time

class UDPBroadcast(threading.Thread):
    
    SERVER_UDP_PORT = 13117
    

    def __init__(self):
        threading.Thread.__init__(self)
        

    def run(self):
        try:
            UDPserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up UDP
            UDPserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
            UDPserver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #broadcast
            UDPserver.bind(('', SERVER_UDP_PORT))
            UDPserver.settimeout(0.2)
            message = bytes("Server started, listening on IP address "+ TCPserverIP, 'utf8')  
            for i in range(WAITING_FOR_CLIENT_COUNT):
                UDPserver.sendto(message, ('<broadcast>', SERVER_UDP_PORT))
                print("message sent!")
                time.sleep(1)
        except Exception as e:
                print("Failed to broadcast messages.\nERROR: "+e)

class ClientThread(threading.Thread):
    def __init__(self, ip, port): 
        threading.Thread.__init__(self) 
        self.ip = ip 
        self.port = port
        print ("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        while True:
            try:
                data = connectionSocket.recv(1048)
            except Exception as e:
                print(e)
            #print_lock.acquire()
            print ("Server received data: %s"%data)
            #print_lock.release()
            #connectionSocket.send(b"message received")  # echo 
            if data == b'exit':
                print("closing connection...")
                break

SERVER_TCP_PORT = 5997
WAITING_FOR_CLIENT_COUNT = 15 # total time for the "waiting for client" mode

threads = []

try:
    TCPserverIP = socket.gethostbyname(socket.gethostname())
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('', SERVER_TCP_PORT))
    server.listen(1)
    print('The server is ready to receive')
    initTime = time.time()
    remainingTime = WAITING_FOR_CLIENT_COUNT # initial remaining time
    while remainingTime>0: 
        socket.settimeout(remainingTime)
        (connectionSocket, (ip, port)) = server.accept()
        newThread = ClientThread(ip, port)
        newThread.start()
        threads.append(newThread)
        remainingTime = WAITING_FOR_CLIENT_COUNT-(time.time()-initTime) #set the remaining time to the server (essentially 10 - time elapsed since start)
except socket.timeout:
    print("timeout caught")
except Exception as e:
    print("TCP server socket failed.\nError: "+str(e))

for t in threads:
    t.join()
      