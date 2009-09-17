#!/usr/bin/env python

from clientProxy import *
import thread
import select
import time
import sys


class Server:

    def __init__(self):
        self.name = str(int(time.time() * 1000))
        self.HOST = ''
        self.PORT = 50000
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []
        self.clients = []
        self.client_lock = thread.allocate_lock()
        print '[ ] Server: ', self.name
        
    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.HOST, self.PORT))
            self.server.listen(self.backlog)
            
        except socket.error, (value, message):
            if self.server:
                self.server.close()
            print "Couldn't open socket: " + message
            sys.exit(1)
            
    def run(self):
        self.open_socket()
        input = [self.server, sys.stdin]
        running = 1
        
        while running:
            inputready, outputready, exceptready = select.select(input, [], [])
            
            for s in inputready:
            
                if s == self.server:
                    # Handle the server socket
                    c = ClientProxy(self, self.server.accept())
                    c.start()
                    self.threads.append(c)
                    
                elif s == sys.stdin:
                    # Handle stdin
                    junk = sys.stdin.readline()
                    running = 0
                    
        # Close all threads
        self.server.close()
        for c in self.threads:
            c.join()
        

    def add_client(self, client_name):
        self.client_lock.acquire()
        if client_name not in self.clients:
            self.clients.append(client_name)
            print '[+] Added client', client_name
        else:
            print '[ ] Client', client_name, 'already in the list'
        self.client_lock.release()


    def rem_client(self, client_name):
        self.client_lock.acquire()
        if client_name in self.clients:
            self.clients.remove(client_name)
            print '[-] Removed client', client_name
        else:
            print '[ ] Client', client_name, 'not in the list'
        self.client_lock.release()


# Execution starts here
if __name__ == "__main__":
    s = Server()
    s.run()
    print '[exit]\n'

