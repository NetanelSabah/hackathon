import socket
import threading
import time

SERVER_TCP_PORT = 5997
IP_ADDRESS = socket.gethostbyname(socket.gethostname())  # change to '127.0.0.1' 
print(IP_ADDRESS)
print_lock = threading.Lock
WAITING_FOR_CLIENT_COUNT = 15
threads = []

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

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(('', SERVER_TCP_PORT))
server.listen(1)
print('The server is ready to receive')

initTime = time.time()
remainingTime = WAITING_FOR_CLIENT_COUNT # initial remaining time
try:
    while 0 < remainingTime:
        server.settimeout(remainingTime)
        (connectionSocket, (ip, port)) = server.accept()
        newThread = ClientThread(ip, port)
        newThread.start()
        threads.append(newThread)    
        remainingTime = WAITING_FOR_CLIENT_COUNT - (time.time() - initTime) #set the remaining time to the server (essentially 10 - time elapsed since start)
        print(str(remainingTime)+"\n")
except socket.timeout:
    print("timeout.")
except Exception as e:
    print("TCP server socket failed.\nError: "+str(e))

for t in threads:
    t.join()