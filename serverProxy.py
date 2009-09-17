from message import *
from listener import *
from executer import *
from Queue import *
import threading
import sys

class ServerProxy:

    def __init__(self, host, port, caller):
        self.host = host
        self.port = port
        self.client = caller
        self.server = ''
        self.connected = False
        self.msg_queue = Queue()
        self.listener = Listener(self.client, self)
        self.executer = Executer(self.client, self)

    
    def connect(self):
        msg = ConnectMessage()
        msg.clientSrc = self.client.name
        msg.data = str(self.client.client_port)
        reply = msg.send(self.host, self.port)

        if msg.type != ErrorMessage:
            self.connected = True
            self.server = msg.serverSrc
            print 'Set Server:', self.server

            self.listener.start()
            self.executer.start()
        else:
            self.print_error(msg.data)
        return msg

        
    def sendMessage(self, message):
        msg = SendMessage()
        msg.clientSrc = self.client.name
        msg.serverDst = self.server
        msg.data = message
        msg.send(self.host, self.port)
        if msg.type == ErrorMessage:
            self.print_error(msg.data)
        return msg

        
    def quit(self):
        if self.executer.is_alive():
            print '[x] Stopping executer...'
            self.msg_queue.put("x")
            self.executer.join()
    
        if self.listener.is_alive():
            print '[x] Stopping listener...'
            self.listener.running = False
            self.listener.join()
           

    def print_error(self, message):
        print '[', self.__class__.__name__, '] Error:', message
        


