from message import *
from listener import *
from executer import *
from Queue import *
import threading
import sys

class ClientProxy:

    def __init__(self, server, (socket, address)):
        threading.Thread.__init__(self)
        self.server = server
        self.socket = client
        self.address = address
        self.size = 1024
        self.connected = False
        self.msg_queue = Queue()
        self.listener = Listener(self.client, self)
        self.executer = Executer(self.client, self)
        
        
    def run(self):
        running = 1
        
        while running:
        
            data = self.socket.recv(self.size)  
            if data:
                msg = Message()
                msg_dict = pickle.loads(data)
                msg.dict2msg(msg_dict)
                print 'Received:', str(msg)
                
                if msg.type == 'ConnectMessage':
                    print 'CONNECT MESSAGE'
                elif msg.type == 'SendMessage':
                    print 'SEND MESSAGE'
                elif msg.type == 'AddClientMessage':
                    print 'ADD CLIENT MESSAGE'
                elif msg.type == 'PingMessage':
                    print 'PING MESSAGE'
                else:
                    print 'UNKNOWN MESSAGE'
                
                # Reply
                msg.clientDst = msg.clientSrc
                msg.clientSrc = ''
                msg.serverSrc = msg.serverDst
                msg.serverDst = ''
                msg.reply(self.socket)

#               if self.connected == False:
#                   self.socket.close()
#                   running = 0
            
