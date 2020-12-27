import socket 

host = socket.gethostname() 
port = 5997
BUFFER_SIZE = 2000 
MESSAGE = input("tcpClientA: Enter message/ Enter exit:") 
 
tcpClientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
tcpClientA.connect((host, port))

while MESSAGE != 'exit':
    tcpClientA.send(bytes(MESSAGE, 'utf-8'))     
    MESSAGE = input("tcpClientA: Enter message to continue/ Enter exit:")
tcpClientA.send(bytes(MESSAGE, 'utf-8'))
tcpClientA.close() 