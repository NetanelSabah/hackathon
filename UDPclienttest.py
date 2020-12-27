import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up UDP
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #allow multiple clients (important)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #broadcast

UDP_PORT = 13118

client.bind(("", UDP_PORT))
while True:
    data, addr = client.recvfrom(1024)
    print("received message: %s"%data)