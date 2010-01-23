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
        self.output(("SERVER %s" % self.__name), logging.INFO)
    
    
    def stop(self):
        self._running = False
        self._kill_dependancies()
            
    
    def _kill_dependancies(self):
        if self.__strategy != None:
            self.output("[x] Exiting strategy...")
            self.__strategy.exit()
        
        if self.__ping_agent != None and self.__ping_agent.is_alive():
            self.output("[x] Killing Ping Agent...")
            self.__ping_agent.stop()
            self.__ping_agent.join(1.0)
            self.__ping_agent = None
    
    
    def set_listener(self, listener):
        self.__listener = listener
    
    
    def set_role(self, role, arg=None):
        if self.__strategy != None:
            self.output("[x] Exiting strategy...")
            self.__strategy.exit()
        
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
    

    def _process_request(self, msg, address):
        #self.output("REQUEST: %s" % str(msg))
        
        # Dynamically call the proper function
        try:
            process_function_name = "_process_" + msg.type
            process_function = getattr(self.__strategy, process_function_name)
        
        except AttributeError:
            self.output("AttributeError (%s.%s)" % (self.__strategy.name, process_function_name), logging.ERROR)
            reply = ErrorMessage(msg.skt, msg.priority)
            reply.serverSrc = self.__name
            reply.clientDst = msg.clientSrc
            reply.data = "Unknown message type: " + msg.type
            self._requests.task_done()
        
        reply = process_function(msg)
        self._requests.task_done()

        if msg.wait_for_reply():
            reply.reply(reply.skt)     


    def _check_recipient(self, msg):
        if msg.serverDst == self.__name:
            return True
        else:
            self.output(("[!] Request for %s, but I am %s" % (msg.serverDst, self.__name)), logging.WARNING)
            return False
        
    
    def query_role(self):
        parser = XMLParser('server_list.xml')
        output_list = parser.get_output_list()
        connected = False
        
        for i in range(len(output_list)):
            # Skip ourselves
            host_and_port = self.__listener.get_host_and_port()
            if output_list[i][0] == host_and_port[0] and int(output_list[i][1]) == host_and_port[1]:
                continue
            
            self.output("Trying %s:%s..." % (output_list[i][0], output_list[i][1]))
            
            # Look for the Master Server
            skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                skt.connect((output_list[i][0], int(output_list[i][1])))
            except socket.error:
                if skt != None:    skt.close()
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
                self.set_role(Server.BACKUP, (reply.serverSrc, (reply.clientSrc, int(reply.clientDst))))
            
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
