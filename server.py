import threading
import socket
from scapy.arch import get_if_addr
import time
import struct
import random
from logAndColor import *

SERVER_UDP_PORT = 13117
SERVER_TCP_PORT = 0
SERVER_IP = get_if_addr('eth1')
BROADCAST_IP = SERVER_IP[:-5]+ '.255.255'

WAITING_FOR_CLIENT_COUNT = 10 # total time for the "waiting for client" mode
# WAITING_FOR_CLIENT_EXTRA = 0.2 # additional time to catch last requests
GAME_MODE_COUNT = 10  # total time for the game mode
CYCLE_WAIT = 10
UDP_TIMEOUT = 0.2  # timeout for UDP server
CALC_WAIT = 0.02  # allows for calculation of the high score for the various client threads

MAGIC_COOKIE = 0xfeedbeef  # UDP header cookie
TYPE = 0x2  # UDP messagetype
PACKET_FORMAT = 'IBH'  # the format for the UDP broadcast messages

player_sockets = {}  # player sockets pool (dictionary of format name:{socket : <val>, thread : <val>, status : <val>})
threads = []  # TCP client threads pool
player_sockets_grouping_list = []
start_game_event = threading.Event()  # signify threads to start the game
result_event = threading.Event() # signify threads that the results are calculated
game_end_flag = False # signify threads to end the game

counters = [0, 0]  # counters[0]: counter for group 1, counters[1]: counter for group 2
counters_lock = threading.Lock()

group1 = []
group2 = []

start_message = ''
end_message = ''

high_score_group = {'name': 'N/A', 'score': 0} 
overall_high_score_player = {'name': 'N/A', 'score': 0}  # for the server's history
current_high_score_player = {'name': 'N/A', 'score': 0}  # for current game
high_score_player_lock = threading.Lock()

def onlyActiveMembers(group): #returns the active members of a given group
    output = []
    for member in group:
        if player_sockets[member]['status'] == True:
            output.append(member)
    return output

# UDP thread
class UDPBroadcast(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            # UDP server setup
            UDP_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # set up UDP
            UDP_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # allow multiple clients (important)
            UDP_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # broadcast
            UDP_server.settimeout(UDP_TIMEOUT)

            # sending broadcast messages
            UDP_message = struct.pack('!IbH', MAGIC_COOKIE, TYPE, SERVER_TCP_PORT)  # encode cookie, type and TCP port
            for i in range(WAITING_FOR_CLIENT_COUNT):  # repeat 10 times
                UDP_server.sendto(UDP_message, (BROADCAST_IP, SERVER_UDP_PORT))
                lowLog("%s) message sent to IP %s!"%(i, BROADCAST_IP))
                time.sleep(1) # wait a second between every broadcast
        except Exception as e:
            print("Failed to broadcast messages via UDP.\nERROR: "+str(e))
        UDP_server.close()
        log("UDP end")

# client thread
class ClientThread(threading.Thread):
    def __init__(self, client_ip, client_port, client_socket):
        threading.Thread.__init__(self)
        self.client_ip = client_ip
        self.client_port = client_port
        self.client_socket = client_socket
        self.client_name = ''
        self.client_counter = 0
        self.client_group = -1
        log("New server socket thread started for " + self.client_ip + ":" + str(self.client_port))

    def run(self):
        try:
            data = self.client_socket.recv(1024)
            result = data.decode('utf8')
            result_length = len(result)
            if result_length > 0 and result[-1] == '\n':  # check if it's a name
                name = result[:-1]
                if player_sockets.get(name) == None:
                    log("player added to pool: %s" % name)
                    self.client_name = name
                    player_sockets[name] = {'connection' : self.client_socket, 'thread': threading.get_ident(), 'status' : True}
                else:
                    log("group with the given name (%s) already exists, closing connection.")
                    self.client_socket.close()
                    return
            else:
                log("got an invalid connection message (does not end with newline), closing connection.")
                self.client_socket.close()
                return

            # wait until game start
            start_game_event.wait()

            # can check only after group game starts, because that's when the teams are sorted
            self.client_group = self.client_name in group2  # 1 if true (group 2), 0 if false (group 1).
            # send 1st message
            self.client_socket.send(bytes(start_message, 'utf-8'))
            log("sent game start message (\"%s...\") to %s/%s" % (start_message[:25], self.client_ip, self.client_port))


            # like waiting for clients, we need to have a timeout on recv incase that the game time is over
            init_game_time = time.time()
            game_time_remaining = GAME_MODE_COUNT
            try:
                while game_time_remaining>0:
                    self.client_socket.settimeout(game_time_remaining)
                    client_data = self.client_socket.recv(1024)
                    if (client_data == b''):
                        raise Exception("Connection lost")
                    val = len(client_data)
                    self.client_counter += val
                    counters_lock.acquire()  # making sure the group counter is synchronized
                    counters[self.client_group] += val
                    lowLog("%s has updated group %s's counter: %s" % (self.client_name, self.client_group+1, counters[self.client_group]))
                    counters_lock.release()
                    game_time_remaining = GAME_MODE_COUNT - (time.time() - init_game_time)
            except socket.timeout:
                pass

            # game over, update the player high-score (if necessary) 
            high_score_player_lock.acquire()
            #all-time high score
            if self.client_counter > overall_high_score_player['score'] or overall_high_score_player['name'] == 'N/A':
                overall_high_score_player['name'] = colorName(self.client_name)
                overall_high_score_player['score'] = self.client_counter
            else:
                if self.client_counter == overall_high_score_player['score']:
                    overall_high_score_player['name']+= '\n' + colorName(self.client_name)
            # current high score
            if self.client_counter > current_high_score_player['score'] or current_high_score_player['name'] == 'N/A':
                current_high_score_player['name'] = colorName(self.client_name)
                current_high_score_player['score'] = self.client_counter
            else:
                if self.client_counter == current_high_score_player['score']:
                    current_high_score_player['name']+= '\n' + colorName(self.client_name)
            high_score_player_lock.release()

            # wait for the ending message to be computed
            result_event.wait()

            self.client_socket.send(bytes(end_message, 'utf-8'))
            log("sent game end message (\"%s...\") to %s/%s" % (end_message[:10], self.client_ip, self.client_port))

        except Exception as e:
            print("Client socket %s/%s failed." %(self.client_ip, self.client_port))
            err("Error: "+str(e))
        log("closing connection with %s/%s..." %(self.client_ip, self.client_port))
        if (player_sockets.get(name) != None):
            player_sockets[name]['status'] = False
        self.client_socket.close()


def main():
    # main thread: TCP server & game control on a loop
    while True:
        # reset values for new game
        threads = []  # thread pool reset
        player_sockets = {}  # player sockets pool for the current game reset
        game_end_flag = False  # new game, reset
        counters = [0, 0]  # reset
        current_high_score_player['name'] = 'N/A'
        current_high_score_player['score'] = 0
        winning_group = -1  # -1 means draw, 0 means group 1 and 1 means group 2

        try:
            # TCP server socket setup
            TCP_server_IP = SERVER_IP  # get the IP for printing the message
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((SERVER_IP, 0))
            (TCP_addr, SERVER_TCP_PORT) = server.getsockname()
            server.listen(1)
            print("Server started, listening on IP address %s in port %s for %s seconds" % (
            TCP_server_IP, SERVER_TCP_PORT, WAITING_FOR_CLIENT_COUNT))

            # UDP thread start
            UDP_thread = UDPBroadcast()
            UDP_thread.start()

            # accept users in TCP
            initTime = time.time()
            remainingTime = WAITING_FOR_CLIENT_COUNT  # initial remaining time
            while remainingTime > 0:
                server.settimeout(remainingTime)  # the timeout will be the remaining time
                (connectionSocket, (ip, port)) = server.accept()
                new_thread = ClientThread(ip, port, connectionSocket)
                new_thread.start()
                threads.append(new_thread)
                # set the remaining time to the server (essentially 10 - time elapsed since start)
                remainingTime = WAITING_FOR_CLIENT_COUNT - (time.time() - initTime)
        except socket.timeout:
            UDP_thread.join()  # timeouts are OK. Wait for UDP to finish
        except Exception as e:
            print("TCP server socket failed, shutting down...")
            err("Error: " + str(e))
            break
        log("Finished listening...")

        # shuffling the clients randomly

        player_sockets_grouping_list = onlyActiveMembers(list(player_sockets.keys()))
        if (len(player_sockets_grouping_list) == 0):
            server.close()
            print("did not find any players, restarting search...")
            continue
        random.shuffle(player_sockets_grouping_list)

        # now, the teams will be assigned in the following order: even - group 1, odd - group 2
        group1 = onlyActiveMembers(player_sockets_grouping_list[::2])
        group2 = onlyActiveMembers(player_sockets_grouping_list[1::2])
        groups = ['\n'.join(map(colorName, group1)), '\n'.join(map(colorName, group2))]

        log("shuffled teams...")
        print("starting game and sending messages to clients")

        # set message to start
        start_message = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n%s\nGroup 2:\n==\n%s\nStart pressing keys on your keyboard as fast as you can!!" % (
        groups[0], groups[1])  # the start message

        start_game_event.set()  # wake all client threads to make them send the message

        time.sleep(GAME_MODE_COUNT)  # wait for 10 seconds

        game_end_flag = True  # signify the client threads to end the game and stop receiving messages

        # calculate results message
        group1_count = counters[0]
        group2_count = counters[1]
        dryRes = "Game over!\nGroup 1 typed in %s characters. Group 2 typed in %s characters.\n" % (
        group1_count, group2_count)
        if group1_count == group2_count:
            victory = "The game ended in a draw!\nCongratulations to both teams!\nGroup 1:\n==\n%s\nGroup 2:\n==\n%s\n" % (
            groups[0], groups[1])
        else:
            winning_group = int(group2_count > group1_count)  # 1 if group 2, 0 if group 1
            victory = "Group %s wins!\nCongratulations to the winners:\n==\n%s\n" % (
            winning_group + 1, groups[winning_group])

        time.sleep(CALC_WAIT)  # wait a moment for the various threads to calculate the highest player score
        if (winning_group == -1):  # draw
            if high_score_group['score'] < counters[0] or high_score_group['name'] == 'N/A':
                high_score_group['name'] = "==\n" + groups[0] + "\n" + "==\n" + groups[1] + "\n"
                high_score_group['score'] = counters[0]
            else:
                if counters[0] == high_score_group['score']:
                    high_score_group['name'] += "==\n" + groups[0] + "\n" + "==\n" + groups[1] + "\n"
        else:
            if high_score_group['score'] < counters[winning_group] or high_score_group['name'] == 'N/A':
                high_score_group['name'] = "==\n" + groups[winning_group] + "\n"
                high_score_group['score'] = counters[winning_group]
            else:
                if counters[winning_group] == high_score_group['score']:
                    high_score_group['name'] += "==\n" + groups[winning_group] + "\n"
        msg_curr_high_score = "\nWith a score of %s each, the highest-scoring players of the game are:\n%s\n" % (
        current_high_score_player['score'], current_high_score_player['name'])
        msg_overall_high_score = "With a score of %s each, the highest-scoring players of the server are:\n%s\n" % (
        overall_high_score_player['score'], overall_high_score_player['name'])
        msg_group_high_score = "With a score of %s each, the highest-scoring groups of the server are:\n%s\n" % (
        high_score_group['score'], high_score_group['name'])

        end_message = dryRes + victory + msg_curr_high_score + msg_overall_high_score + msg_group_high_score

        result_event.set()  # notify the threads to post the results
        print("sending results (\"%s...\") to players..." % (end_message[:10]))

        for t in threads:  # waiting for the last client threads to end
            t.join()

        server.close()  # now, we can kill the server and restart and kill themselves
        log("closing the server and re-opening it...")
        time.sleep(CYCLE_WAIT)

if __name__ == "__main__":
    main()
