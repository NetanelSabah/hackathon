import socket
import threading

SERVER_TCP_PORT = 5997
IP_ADDRESS = '127.0.0.1'  # change to socket.gethostbyname(socket.gethostname())

print_lock = threading.Lock
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

while True:
    (connectionSocket, (ip, port)) = server.accept()
    newThread = ClientThread(ip, port)
    newThread.start()
    threads.append(newThread)

for t in threads:
    t.join()