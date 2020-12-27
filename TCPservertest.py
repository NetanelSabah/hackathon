import socket

SERVER_TCP_PORT = 5997
IP_ADDRESS = '127.0.0.1'  # change to socket.gethostbyname(socket.gethostname())

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(('', SERVER_TCP_PORT))
server.listen(1)
print('The server is ready to receive')

while True:
    
