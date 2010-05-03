'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from serverStrategies.masterStrategy import *
from serverStrategies.backupStrategy import *
from serverStrategies.idleStrategy import *
from utilities.pingAgent import *
from utilities.xmlParser import *
import time

class Server(ActiveObject):
    
    # Server roles
    MASTER = 'MasterStrategy'
    BACKUP = 'BackupStrategy'
    IDLE = 'IdleStrategy'

    def __init__(self, role = 'undefined'):
        ActiveObject.__init__(self)
        self.__name = str(int(time.time() * 1000))
        self.__listener = None
        self.__strategy = None
        self.__ping_agent = None
        self.servers = {}           # List of Servers: (name, (ip, port))
        self.clients_ping = {}      # Clients ping timestamps (name, last_ping_ts)
        self.servers_lock = threading.Lock()
        self.clients = {}           # List of Clients
        self.servers_ping = {}      # Servers ping timestamps (name, last_ping_ts)
        self.clients_lock = threading.Lock()
        self.output(("SERVER %s" % self.__name), logging.INFO)
    
    
    def stop(self):
        self._running = False
        self._kill_dependancies()
            
    
    def _kill_dependancies(self):
        """De-initialise any related instance and thread."""
        if self.__strategy is not None:
            self.output("[x] Exiting strategy...")
            self.__strategy.exit()
        
        if self.__ping_agent is not None and self.__ping_agent.is_alive():
            self.output("[x] Killing Ping Agent...")
            self.__ping_agent.stop()
            self.__ping_agent.join(1.0)
            self.__ping_agent = None
    
    
    def set_listener(self, listener):
        self.__listener = listener
    
    
    def set_role(self, role, arg=None):
        """Set a new strategy."""
        self._kill_dependancies()
        
        self.output("Setting role: %s" % role)
        
        # Dynamically create the proper class
        try:
            self.__strategy = globals()[role](self, arg)
        except KeyError:
            self.output(("[!] ROLE \"%s\" DOESN'T MAP ANY CLASS!!!\n" % role), logging.CRITICAL)
            return
        
        # Start the Ping Agent
        self.__ping_agent = PingAgent(caller=self, run_as_server=True)
        if not self.__ping_agent.isAlive():
            self.__ping_agent.start()
        
    
    def get_role(self):
        return self.__strategy
        
    
    def get_name(self):
        return self.__name
    
    
    def get_client_list(self):
        """Return the list of connected Clients as a tuple."""
        c_names = []
        c_ip = []
        c_port = []
        
        self.clients_lock.acquire()
        for c in self.clients.keys():
            c_names.append(c)
            c_ip.append(self.clients[c][0])
            c_port.append(self.clients[c][1])
        self.clients_lock.release()
        
        return (c_names, c_ip, c_port)
    
    
    def print_client_list(self):
        """Print the Client list."""
        self.clients_lock.acquire()
        self.output("Clients:")
        if len(self.clients) == 0:
            self.output("None")
        else:
            for c in self.clients.keys():
                self.output((c, self.clients[c]))
        self.clients_lock.release()
    
    
    def print_server_list(self):
        """Print the Server list."""
        self.servers_lock.acquire()
        self.output("Servers:")
        if len(self.servers) == 0:
            self.output("None")
        else:
            for s in self.servers.keys():
                self.output((s, self.servers[s]))
        self.servers_lock.release()
    
    
    def get_server_list(self):
        """Return the list of connected Servers as a tuple."""
        s_names = []
        s_ip = []
        s_port = []
        
        self.servers_lock.acquire()
        for s in self.clients.keys():
            s_names.append(s)
            s_ip.append(self.clients[s][0])
            s_port.append(self.clients[s][1])
        self.servers_lock.release()
        
        return (s_names, s_ip, s_port)
    

    def _process_request(self, msg, type):
        process_function = None
        process_function_name = None
        
        # Dynamically call the proper function
        try:
            if type == self.LOCAL_REQUEST:
                self.output("PROCESSING %s..." % msg.data, logging.DEBUG)
                process_function = getattr(self.__strategy, msg.data)
                    
            elif type == self.REMOTE_REQUEST:
                process_function_name = "_process_" + msg.type
                process_function = getattr(self.__strategy, process_function_name)
                
            else:
                self.output("Invalid request type: %d" % type, logging.ERROR)
            
        except AttributeError:
            self.output("AttributeError (%s.%s)" % (self.__strategy.name, process_function_name), logging.ERROR)
            reply = ErrorMessage(msg.skt, msg.priority)
            reply.serverSrc = self.__name
            reply.clientDst = msg.clientSrc
            reply.data = "Unknown message type: " + msg.type
            self._requests.task_done()
        
        # Execute the request
        if process_function is not None:
            if type == self.LOCAL_REQUEST:
                process_function()
            elif type == self.REMOTE_REQUEST:
                reply = process_function(msg)
                if msg.wait_for_reply():
                    reply.reply(reply.skt)
            else:
                self.output("Invalid request type: %d" % type, logging.ERROR)
        
        # We're done
        self._requests.task_done()


    def _check_recipient(self, msg):
        if msg.serverDst == self.__name:
            return True
        else:
            self.output(("[!] Request for %s, but I am %s" % (msg.serverDst, self.__name)), logging.WARNING)
            return False
        
    
    def query_role(self):
        """
        Try to connect to each Server in the file and ask for a role.
        If no one replies, we are the Master.
        """
        parser = XMLParser('server_list.xml')
        server_list = parser.get_output_list()
        connected = False
        
        for i in range(len(server_list)):
            # Skip ourselves
            host_and_port = self.__listener.get_host_and_port()
            if server_list[i][0] == host_and_port[0] and int(server_list[i][1]) == host_and_port[1]:
                continue
            
            self.output("Trying %s:%s..." % (server_list[i][0], server_list[i][1]))
            
            # Look for the Master Server
            skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                skt.connect((server_list[i][0], int(server_list[i][1])))
            except socket.error:
                if skt != None:
                    skt.close()
                continue
    
            # Send 'Hello' message
            msg = HelloMessage(use_socket=skt, priority=1)
            msg.serverSrc = self.__name         # Our Name
            msg.clientSrc = self.ip             # Our IP address
            msg.clientDst = str(self.port)      # Our Port
            reply = msg.send()
            if reply is not None:
                connected = True
            if skt is not None:
                skt.close()

            if reply.type == 'ErrorMessage':
                continue    # Oops, it wasn't the Master Server
            
            elif reply.type == 'WelcomeBackupMessage':
                self.set_role(Server.BACKUP, (reply, (server_list[i][0], int(server_list[i][1]))))
            
            elif reply.type == 'WelcomeIdleMessage':
                self.set_role(Server.IDLE, (reply.serverSrc, (reply.clientSrc, int(reply.clientDst))))
            
            else:
                self.output(("UNKNOWN ROLE: %s" % reply.type), logging.ERROR)
                self.set_role(reply.type)
            # We're done
            return
        
        # We're the Master Server
        if connected == False:
            self.set_role(Server.MASTER)
