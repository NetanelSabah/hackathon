import socket
import time

SERVER_PORT = 2092
UDP_PORT = 13118

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up UDP
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #broadcast
server.bind(('127.0.0.1', SERVER_PORT))

server.settimeout(0.2)
message = b"important message"
while True:
    server.sendto(message, ('<broadcast>', UDP_PORT))
    print("message sent!")
    time.sleep(1)