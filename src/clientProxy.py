'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from utilities.xmlParser import *
from utilities.pingAgent import *
import time


class ClientProxy(ActiveObject):
    
    def __init__(self, ip, port):
        ActiveObject.__init__(self)
        self.__name = str(int(time.time() * 1000))
        self.skt = None
        self.ip = ip
        self.port = port
        self.master_ip = None
        self.master_port = None
        self.master_name = None
        self.__listener = None
        self.__clients = []
        self.__connected = False
        self.__ping_agent = None
        self.interface = None
        self.output(("CLIENT %s" % self.__name), logging.INFO)
    
    
    def kill(self):
        if self.__ping_agent is not None:
            self.__ping_agent.stop()
            self.__ping_agent.join(2.0)
        self.output("[x] ClientProxy", logging.INFO)
    
    
    def get_name(self):
        return self.__name
    
    
    def set_listener(self, listener):
        self.__listener = listener
        
    
    def connect(self):
        """Connect to a Server."""
        parser = XMLParser('server_list.xml')
        server_list = parser.get_output_list()
        self.__connected = False
        
        for i in range(len(server_list)):
            self.output("Connecting to %s:%s..." % (server_list[i][0], server_list[i][1]))
            if self.connect_to_server(server_list[i][0], int(server_list[i][1])):
                break
        
        if not self.__connected:
            self.output("No server found!", logging.CRITICAL)
            return False
        
        else:
            self.output("Connected to %s (%s:%d)" % (self.master_name, self.master_ip, self.master_port))
            self.interface.set_status("Connected to %s" % self.master_name)
            
            # Start the Ping Agent
            self.__ping_agent = PingAgent(caller=self, run_as_server=False)
            self.__ping_agent.start()
            return True
    
    
    def send_message(self, destination, message):
        """Send a message to destination Client."""
        if not self.__connected or self.skt is None:
            self.interface.set_status("Not connected to server")
            return None 
        
        if destination not in self.__clients:
            self.interface.set_status("Destination %s doesn't exists" % destination)
            return None
        
        self.output(("Sending \"%s\" to %s" % (message, destination)), logging.DEBUG)
        
        # Create the message to send
        msg = SendMessage()
        msg.clientSrc = self.__name
        msg.clientDst = destination
        msg.serverDst = self.master_name
        msg.data = message
        
        # Send the message
        reply = msg.send(self.master_ip, self.master_port)
        if reply is None:
            if self.interface is not None:
                self.interface.print_message("Error sending message to %s: %s" % (destination, msg.data))
        
        return reply
    

    def _process_request(self, msg, type):
        """Process a received request by dynamically calling the proper method."""
        try:
            process_function_name = "_process_" + msg.type
            process_function = getattr(self, process_function_name)
        
        except AttributeError:
            reply = ErrorMessage(msg.skt, msg.priority)
            reply.serverSrc = self.__name
            reply.clientDst = msg.clientSrc
            reply.data = "Unknown message type: " + msg.type
        
        reply = process_function(msg)
        self._requests.task_done()

        if msg.wait_for_reply():
            reply.reply(reply.skt)
    
        
    def _process_SendMessage(self, msg):
        """Display the received Message."""
        print 'Processing SendMessage'
        
        if self.interface is not None:
            self.interface.print_message("%s: %s" % (msg.clientSrc, msg.data))
        
        if msg.skt is None:
            return None
        
        reply = Message(msg.skt, msg.priority)
        reply.clientSrc = self.__name
        reply.clientDst = msg.clientSrc
        reply.serverDst = msg.serverSrc
        return reply

    
    def _process_PingMessage(self, msg):
        print 'Processing PingMessage'
        # TODO
        
    
    def _process_errorMessage(self, msg):
        print 'Processing ErrorMessage'
        # TODO
    
    
    def _process_SyncClientListMessage(self, msg):
        """Update the list of connected Clients."""
        self.output(("Received ClientList from %s" % msg.serverSrc), logging.INFO)
        c_names = pickle.loads(msg.data)
        
        self.__update_client_list(c_names)
        
        reply = SyncClientListMessage(msg.skt, msg.priority)
        reply.clientSrc = self.__name
        reply.serverDst = msg.serverSrc
        return reply
    
    
    def _process_NewMasterMessage(self, msg):
        """Master has changed: update related information."""
        self.master_name = msg.data
        self.master_ip = msg.clientSrc
        self.master_port = int(msg.serverDst)
        
        self.output(("New Master is %s (%s:%d)" % (self.master_name,
                                                   self.master_ip,
                                                   self.master_port)),
                                                   logging.INFO)
        
        self.interface.set_status("Connected to %s" % self.master_name)
        
        reply = NewMasterMessage(msg.skt, msg.priority)
        reply.clientSrc = self.__name
        reply.serverDst = msg.serverSrc
        return reply
    
    
    def connect_to_server(self, server_ip, server_port):
        """
        Connect to the specified Server.
        Try until connected to the Master server, or until there are no Servers left.
        """
        if self.skt is not None:
            # Close previous socket
            self.skt.close()
            self.skt = None
        
        # Create a new socket and try connecting
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.skt.connect((server_ip, server_port))
        except socket.error:
            if self.skt:
                self.skt.close()
                self.skt = None
            return False

        # Send 'Hello' message
        msg = ConnectMessage(use_socket=self.skt, priority=1)
        msg.clientSrc = self.__name         # Our Name
        msg.serverDst = self.ip             # Our IP address
        msg.data = str(self.port)           # Our Port
        reply = msg.send()
        
        if reply is not None and reply.type != 'SyncClientListMessage':
            # Oops, it wasn't the Master Server
            self.output("Oops, wrong server!", logging.WARNING)
            if self.skt:
                self.skt.close()
                self.skt = None
            return False
            
        else:
            # We found the Master Server
            self.master_ip = server_ip
            self.master_port = server_port
            self.master_name = reply.serverSrc
            
            # Update clients list
            if reply.data is not None:
                c_names = pickle.loads(reply.data)
                self.__update_client_list(c_names)
                self.__connected = True
            return True
            
    
    def __update_client_list(self, client_list):
        """Update the Client list and display in on the interface."""
        # Clear the clients list
        while len(self.__clients):
            self.__clients.pop()
            # Update the interface
            if self.interface is not None:
                self.interface.clearClientListCallback()
        
        for i in client_list:
            if i != self.__name:
                self.__clients.append(i)
                # Update the interface, if any
                if self.interface is not None:
                    self.interface.addClientCallback(i)
        
        # Print ClientProxy list (debug)
        self.output("CLIENT LIST (%d clients except me)" % len(self.__clients))
        for c in self.__clients:
            self.output("%s" % c)
