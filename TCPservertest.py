import socket
import threading

SERVER_TCP_PORT = 5997
IP_ADDRESS = '127.0.0.1'  # change to socket.gethostbyname(socket.gethostname())

print_lock = threading.Lock

class ClientThread(Thread):
    def __init__(self, ip, port, conn): 
        threading.Thread.__init__(self) 
        self.ip = ip 
        self.port = port
        self.conn = conn
        print ("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        while True:
            data = conn.recv(1048)
            print ("Server received data:" + data)
            MESSAGE = b"Multithreaded Python server : Enter Response from Server/Enter exit:"
            if MESSAGE == b"exit":
                break
            conn.send(MESSAGE)  # echo 

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(('', SERVER_TCP_PORT))
server.listen(1)
print('The server is ready to receive')

while True:
    connectionSocket, clientAddress = server.accept()

