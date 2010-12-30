'''
Created on 22 Sep 2009

@author: piero
'''

from serverStrategy import *


class IdleStrategy(ServerStrategy):
    
    def __init__(self, server, master=None):
        self.__server = server
        self.name = self.__server.IDLE
        self.__master = master
        self.__server.output("Behaviour: %s" % self.name)
        if self.__master != None:
            self.__server.output("(master: %s)" % self.__master[0])

        
    def get_master(self):
        return self.__master
        
    
    def _process_ConnectMessage(self, msg):
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.clientSrc = self.__master[1][0]           # Master IP address
        reply.serverDst = str(self.__master[1][1])      # Master Port
        reply.data = self.__master[0]                   # Master Name
        return reply
    
    
    def _process_SendMessage(self, msg):
        # TODO
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.data = "Unknown message type: " + msg.type
        return reply
    
    
    def _process_PingMessage(self, msg):
        # TODO
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.data = "Unknown message type: " + msg.type
        return reply
    
    
    def _process_ErrorMessage(self, msg):
        # TODO
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.data = "Unknown message type: " + msg.type
        return reply
    
    
    def _process_HelloMessage(self, msg):
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.clientSrc = self.__master[1][0]           # Master IP address
        reply.clientDst = str(self.__master[1][1])      # Master Port
        reply.data = self.__master[0]                   # Master Name
        return reply
    
    
    def _process_BecomeMasterMessage(self, msg):
        self.__server.set_role(self.__server.MASTER, msg)
        
        reply = BecomeMasterMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.data = ""
        return reply
    
    
    def _process_NewMasterMessage(self, msg):
        new_master = (msg.data, (msg.clientSrc, int(msg.clientDst)))
        self.__server.output("Updating Master: %s (%s:%d)" % (new_master[0],
                                                            new_master[1][0],
                                                            new_master[1][1]))
        self.__master = new_master
        
        reply = NewMasterMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.data = ""
        return reply


    def _process_BecomeBackupMessage(self, msg):
        """Become the new Backup server"""
        master_ip_and_port = pickle.loads(msg.clientSrc)
        self.__server.set_role(self.__server.BACKUP, (msg, (master_ip_and_port[0], master_ip_and_port[1])))

        reply = BecomeBackupMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        return reply
    