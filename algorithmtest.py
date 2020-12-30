import socket
import netifaces

list = ['Hello', 'My', 'Name', 'Is', 'Harry']
print('\n'.join(list[::2]))
print("----\n\n----")
print('\n'.join(list[1::2]))

SERVER_IP = netifaces.ifaddresses('eth1')
print (SERVER_IP + "\n\n")