from message import *
import threading
import sys
import select

class ServerProxy:

    def __init__(self, host, port, caller):
        self.host = host
        self.port = port
        self.client = caller
        self.server = ''
        self.connected = False
        self.listener = ListenerThread(self.client)
    
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
        

class ListenerThread(threading.Thread):

    def __init__(self, caller):
        threading.Thread.__init__(self)
        self.client = caller
        self.skt = None
        self.backlog = 5
        self.running = False
    
    def open_socket(self):
        try:
            self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.skt.bind((self.client.client_ip, self.client.client_port))
            print 'Listening on port', self.client.client_port, '...'
            self.skt.listen(self.backlog)
            
        except socket.error, (value, message):
            if self.skt:
                self.skt.close()
            print "Couldn't open socket: " + message
            sys.exit(1)
    
    def run(self):
        self.open_socket()
        input = [self.skt, sys.stdin]
        self.running = True
        
        while self.running:
            inputready, outputready, exceptready = select.select(input, [], [], 1.0)

            for s in inputready:
    
                if s == self.skt:
                    # Handle server socket
                    client_skt, address = s.accept()
                    print 'New connection from', address
                    input.append(client_skt)
                    
                elif s == sys.stdin:
                    # Handle stdin
                    pass
            
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
                        msg.reply(s)
                    else:
                        s.close()
                        input.remove(s)
