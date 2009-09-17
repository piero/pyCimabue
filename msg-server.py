#!/usr/bin/env python

from clientProxy import *
import select
import socket
import sys
import time


class Server:

    def __init__(self, host = 'localhost', port = 50000):
        self.name = str(int(time.time() * 1000))
        self.HOST = host
        self.PORT = port
        self.backlog = 5
        self.size = 1024
        self.clients = {}
        print '[ ] Server:', self.name

    def run(self):
        try:
            server_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_skt.bind((self.HOST, self.PORT))
            print 'Listening on port', self.PORT, '...'
            server_skt.listen(self.backlog)

        except socket.error, (value, message):
            if server_skt:
                server_skt.close()
            print 'Couldn\'t open socket:', message
            sys.exit(1)

        input = [server_skt, sys.stdin]
        running = 1

        while running:
            inputready, outputready, exceptready = select.select(input, [], [])

            for s in inputready:
    
                if s == server_skt:
                    # Handle server socket
                    client_skt, address = s.accept()
                    print 'New connection from', address
                    input.append(client_skt)
            
                elif s == sys.stdin:
                    # Handle stdin: exit
                    junk = sys.stdin.readline()
                    running = 0
            
                else:
                    # Handle a client socket
                    data = s.recv(self.size)
            
                    if data:
                        msg = Message()
                        msg_dict = pickle.loads(data)
                        msg.dict2msg(msg_dict)
                        print 'Received:', str(msg)
                
                        if msg.type == 'ConnectMessage':
                            print 'CONNECT MESSAGE'
                            self.addClient(name = msg.clientSrc, ip = address[0], port = msg.data)
                        elif msg.type == 'SendMessage':
                            print 'SEND MESSAGE'
                        elif msg.type == 'AddClientMessage':
                            print 'ADD CLIENT MESSAGE'
                        elif msg.type == 'PingMessage':
                            print 'PING MESSAGE'
                        else:
                            print 'UNKNOWN MESSAGE'
                
                        # Reply
                        reply = ConnectMessage()
                        reply.clientDst = msg.clientSrc
                        reply.serverSrc = self.name
                        reply.reply(s)
                    else:
                        s.close()
                        input.remove(s)

        # Exit
        server_skt.close()
        
        
    def addClient(self, name, ip, port):
        if name not in self.clients:
            self.clients[name] = (ip, port)
            print '[+]', name, ':', self.clients[name]
        else:
            print '[!]', name, 'already exists'
    

# Execution starts here
if __name__ == "__main__":
    s = Server()
    s.run()
    print '[exit]\n'

