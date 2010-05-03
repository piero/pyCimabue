'''
Created on 22 Sep 2009

@author: piero
'''

from serverStrategy import *


class BackupStrategy(ServerStrategy):
    
    def __init__(self, server, arg=None):
        """
        arg = (Message, (Master_IP, Master_port))
        """
        self.__server = server
        self.name = self.__server.BACKUP
        
        # Set the Master
        self.__master = (arg[0].serverSrc, (arg[1][0], arg[1][1]))
        
        self.__server.output("Behaviour: %s" % self.name)
        if self.__master != None:
            self.__server.output("(Master: %s (%s:%d)" % (self.__master[0], self.__master[1][0], self.__master[1][1]))
        
        # Set the Client list, if any
        if arg[0].data != "":
            self.__server.clients_lock.acquire()
            self.__server.clients = pickle.loads(arg[0].data)
            self.__server.clients_lock.release()
            self.__server.print_client_list()
        
        # Set the Server list, if any
        if arg[0].clientDst != "":
            self.__server.servers_lock.acquire()
            self.__server.servers = pickle.loads(arg[0].clientDst)
            self.__server.servers_lock.release()
            self.__server.print_server_list()
        

    def get_master(self):
        """Return our Master."""
        return self.__master
    
    
    def elect_new_master(self):
        """
        Elect a new Master.
        If there isn't any Server available, we become the new Master.
        """
        self.__server.output("Electing a new Master...", logging.INFO)
        self.__master = None
        
        self.__server.servers_lock.acquire()
        
        while len(self.__server.servers) > 0:
            # 1) Get a candidate
            curr = self.__server.servers.iteritems()
            candidate = curr.next()
            self.__server.output(("Candidate: [%s] %s:%d" % (candidate[0], candidate[1][0], candidate[1][1])), logging.INFO)
        
            # 2) Notify it
            elect_msg = BecomeMasterMessage(priority=0)
            elect_msg.serverSrc = self.__server.get_name()  # Candidate name
            elect_msg.serverDst = candidate[0]              # Candidate IP 
            elect_msg.clientSrc = self.__server.ip          # Our IP
            elect_msg.clientDst = str(self.__server.port)   # Our port
            reply = elect_msg.send(candidate[1][0], candidate[1][1])
            
            # 3) If successful, we can break the loop
            if reply is not None and reply.type != ErrorMessage:
                del self.__server.servers[candidate[0]]    # Remove the new Master from the Servers list
                self.__master = candidate           # and set it as our Master
                self.__server.output("New Master is %s (%s:%d)" % (self.__master[0],
                                                        self.__master[1][0],
                                                        self.__master[1][1]),
                                                        logging.INFO)
                break
            
            # 4) Else remove the Server from our Servers list and try another one
            else:
                self.__server.output("Candidate %s is down" % candidate[0])
                del self.__server.servers[candidate[0]]
        
        self.__server.servers_lock.release()
        
        # 5) If the list is empty, we become the new Master
        if len(self.__server.servers) == 0 and self.__master is None:
            self.__server.output("No more candidates: I am the Master", logging.INFO)
            self.__master = self.__server
    
        # 6) If necessary, update the Master's Client list
        if self.__master != self.__server:
            if self.sync_client_list() == False:
                return False
        
        # 7) Notify connected Clients
        self.__notify_clients()
        
        # 8) If necessary, update the Master's Server list
        if self.__master != self.__server:
            if self.sync_server_list() == False:
                return False
        
        # 9) Notify Idle Servers
        self.__notify_servers()
        
        # 10) If I shall become the Master, do it
        if self.__master == self.__server:
            self.__server.set_role(self.__server.MASTER)
        
        return True
    
    
    def sync_client_list(self):
        """Synchronize Client list on a newly elected Master."""
        if self.__master is None:
            return False
        
        master_update = SyncClientListMessage(priority=0)
        master_update.serverSrc = self.__server.get_name()
        master_update.serverDst = self.__master
        master_update.data = pickle.dumps(self.__server.clients)
        reply = master_update.send(self.__master[1][0], self.__master[1][1])
        
        if reply is None or reply == ErrorMessage:
            self.__server.output("[!] Error synchronizing client list on Master")
            self.__server.output(">>> %s" % master_update.data)
            return False
        else:
            self.__server.output("Synchronized client list on Master")
            return True
        
    
    def sync_server_list(self):
        """Synchronize Server list on a newly elected Master."""
        if self.__master is None:
            return False
        
        master_update = SyncServerListMessage(priority=0)
        master_update.serverSrc = self.__server.get_name()
        master_update.serverDst = self.__master
        master_update.data = pickle.dumps(self.__server.servers)
        reply = master_update.send(self.__master[1][0], self.__master[1][1])
        
        if reply is None or reply == ErrorMessage:
            self.__server.output("[!] Error synchronizing server list on Master")
            self.__server.output(">>> %s" % master_update.data)
            return False
        else:
            self.__server.output("Synchronized server list on Master")
            return True
    
    
    def __notify_clients(self):
        """Notify Clients that Master has changed."""
        self.__server.clients_lock.acquire()
        for c in self.__server.clients.keys():
            notify_client_msg = NewMasterMessage(priority=0)
            notify_client_msg.serverSrc = self.__server.get_name()
            notify_client_msg.clientDst = c[0]
            
            if self.__master == self.__server:
                notify_client_msg.clientSrc = self.__server.ip          # Our IP
                notify_client_msg.serverDst = str(self.__server.port)   # Our port
                notify_client_msg.data = self.__server.get_name()       # Our name
            else:
                notify_client_msg.clientSrc = self.__master[1][0]       # Master IP
                notify_client_msg.serverDst = str(self.__master[1][1])  # Master port
                notify_client_msg.data = self.__master[0]               # Master name
            
            client = self.__server.clients[c]
            self.__server.output("Notifying client %s (%s:%d)..." % (c, client[0], client[1]))
            reply = notify_client_msg.send(client[0], client[1])
            
            if reply is None or reply == ErrorMessage:
                self.__server.output("Error notifying client %s (%s:%d)" %
                                     (c, client[0], client[1]), logging.ERROR)
                self.__server.output(">>> %s" % notify_client_msg.data)
                del self.__server.clients[c[0]]
        self.__server.clients_lock.release()
    
    
    def __notify_servers(self):
        """Notify other Servers that Master has changed."""
        for s in self.__server.servers.keys():
            notify_server_msg = NewMasterMessage(priority=0)
            notify_server_msg.serverSrc = self.__server.get_name()
            notify_server_msg.serverDst = s[0]
            
            if self.__master == self.__server:
                notify_server_msg.clientSrc = self.__server.ip         # Our IP
                notify_server_msg.clientDst = str(self.__server.port)  # Our port
                notify_server_msg.data = self.__server.get_name()      # Our name
            else:
                notify_server_msg.clientSrc = self.__master[1][0]      # Master IP
                notify_server_msg.clientDst = str(self.__master[1][1]) # Master port
                notify_server_msg.data = self.__master[0]              # Master name
                
            srv = self.__server.servers[s]
            self.__server.output("Notifying server %s (%s:%d)..." % (s, srv[0], srv[1]))
            reply = notify_server_msg.send(srv[0], srv[1])
            
            if reply is None or reply == ErrorMessage:
                self.__server.output("Error notifying server %s (%s:%d)" %
                                     (s, srv[0], srv[1]),
                                     logging.ERROR)
                self.__server.output(">>> %s" % notify_server_msg.data)
    
    
    def _process_ConnectMessage(self, msg):
        # TODO
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.data = "Unknown message type: " + msg.type
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
        """Return an Error Message, since we're not the Master."""
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        reply.clientSrc = self.__master[1][0]           # Master IP address
        reply.clientDst = str(self.__master[1][1])      # Master Port
        reply.data = self.__master[0]                   # Master Name
        return reply
    
    
    def _process_SyncServerListMessage(self, msg):
        """Update our Server list."""
        self.__server.output(("Received ServerList from %s" % msg.serverSrc), logging.INFO)
        
        self.__server.servers_lock.acquire()
        self.__server.servers.clear()
        self.__server.servers = pickle.loads(msg.data)
        self.__server.servers_lock.release()
        self.__server.print_server_list()

        reply = SyncServerListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        return reply


    def _process_SyncClientListMessage(self, msg):
        """Update our Client list."""
        self.__server.output(("Received ClientList from %s" % msg.serverSrc), logging.INFO)
        
        self.__server.clients_lock.acquire()
        self.__server.clients.clear()
        self.__server.clients = pickle.loads(msg.data)
        self.__server.clients_lock.release()
        self.__server.print_client_list()
        
        reply = SyncClientListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        return reply
