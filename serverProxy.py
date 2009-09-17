from message import *
from listener import *
import threading
import sys

class ServerProxy:

    def __init__(self, host, port, caller):
        self.host = host
        self.port = port
        self.client = caller
        self.server = ''
        self.connected = False
        self.listener = Listener(self.client)
    
    def connect(self):
        msg = ConnectMessage()
        msg.clientSrc = self.client.name
        msg.data = str(self.client.client_port)
        msg.send(self.host, self.port)
        if msg.type != ErrorMessage:
            self.connected = True
            self.listener.start()
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
        if self.listener.is_alive():
            print '[x] Stopping listener...'
            self.listener.running = False
            self.listener.join()
            print '[x] Listener has stopped'        

    def print_error(self, message):
        print '[', self.__class__.__name__, '] Error:', message
        


