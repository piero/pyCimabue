'''
Created on 22 Sep 2009

@author: piero
'''

from serverStrategy import *


class BackupStrategy(ServerStrategy):
    
    def __init__(self, server, master=None):
        self.__server = server
        self.name = self.__server.BACKUP
        self.__master = master
        self.__servers = {}
        self.__clients = {}
        self.__servers_lock = threading.Lock()
        self.__clients_lock = threading.Lock()
        self.__server.output("Behaviour: %s" % self.name)
        if self.__master != None:
            self.__server.output("(master: %s)" % self.__master[0])
            

    def get_master(self):
        return self.__master
    
    
    def elect_new_master(self):
        self.__server.output("Electing a new Master...", logging.INFO)
        self.__master = None
        
        self.__servers_lock.acquire()
        
        while len(self.__servers) > 0:
            # 1) Get a candidate
            curr = self.__servers.iteritems()
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
                del self.__servers[candidate[0]]    # Remove the new Master from the Servers list
                self.__master = candidate           # and set it as our Master
                self.__server.output("New Master is %s (%s:%d)" % (self.__master[0],
                                                        self.__master[1][0],
                                                        self.__master[1][1]),
                                                        logging.INFO)
                break
            
            # 4) Else remove the Server from our Servers list and try another one
            else:
                self.__server.output("Candidate %s is down" % candidate[0])
                del self.__servers[candidate[0]]
        
        self.__servers_lock.release()
        
        # 5) If the list is empty, we become the new Master
        if len(self.__servers) == 0 and self.__master is None:
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
        if self.__master is None:
            return False
        
        c_names = []
        c_ip = []
        c_port = []
        
        self.__clients_lock.acquire()
        for c in self.__clients.keys():
            c_names.append(c)
            c_ip.append(self.__clients[c][0])
            c_port.append(self.__clients[c][1])
        self.__clients_lock.release()
        
        master_update = SyncClientListMessage(priority=0)
        master_update.serverSrc = self.__server.get_name()
        master_update.serverDst = self.__master
        master_update.clientSrc = pickle.dumps(c_ip)    # Client IPs
        master_update.clientDst = pickle.dumps(c_port)  # Client ports
        master_update.data = pickle.dumps(c_names)      # Client names
        reply = master_update.send(self.__master[1][0], self.__master[1][1])
        
        if reply is None or reply == ErrorMessage:
            self.__server.output("[!] Error synchronizing client list on Master")
            self.__server.output(">>> %s" % master_update.data)
            return False
        else:
            return True
        
    
    def sync_server_list(self):
        if self.__master is None:
            return False
        
        s_names = []
        s_ip = []
        s_port = []
        
        self.__servers_lock.acquire()
        for s in self.__servers.keys():
            s_names.append(s)
            s_ip.append(self.__servers[s][0])
            s_port.append(self.__servers[s][1]) 
        self.__servers_lock.release()
        
        master_update = SyncServerListMessage(priority=0)
        master_update.serverSrc = self.__server.get_name()
        master_update.serverDst = self.__master
        master_update.clientSrc = pickle.dumps(s_ip)    # Server IPs
        master_update.clientDst = pickle.dumps(s_port)  # Server ports
        master_update.data = pickle.dumps(s_names)      # Server names
        reply = master_update.send(self.__master[1][0], self.__master[1][1])
        
        if reply is None or reply == ErrorMessage:
            self.__server.output("[!] Error synchronizing server list on Master")
            self.__server.output(">>> %s" % master_update.data)
            return False
        else:
            return True
    
        
    def __notify_clients(self):
        self.__clients_lock.acquire()
        for c in self.__clients.keys():
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
            
            client = self.__clients[c]
            self.__server.output("Notifying client %s (%s:%d)..." % (c, client[0], client[1]))
            reply = notify_client_msg.send(client[0], client[1])
            
            if reply is None or reply == ErrorMessage:
                self.__server.output("Error notifying client %s (%s:%d)" %
                                     (c, client[0], client[1]), logging.ERROR)
                self.__server.output(">>> %s" % notify_client_msg.data)
                del self.__clients[c[0]]
        self.__clients_lock.release()
    
    
    def __notify_servers(self):
        for s in self.__servers.keys():
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
                
            srv = self.__servers[s]
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
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        reply.clientSrc = self.__master[1][0]            # Master IP address
        reply.clientDst = str(self.__master[1][1])        # Master Port
        reply.data = self.__master[0]                    # Master Name
        return reply
    
    
    def _process_SyncServerListMessage(self, msg):
        self.__server.output(("Received ServerList from %s" % msg.serverSrc), logging.INFO)
        s_name = pickle.loads(msg.clientSrc)
        s_ip = pickle.loads(msg.clientDst)
        s_port = pickle.loads(msg.data)
        
        self.__servers_lock.acquire()
        self.__servers.clear()
        
        for i in range(len(s_name)):
            self.__servers[s_name[i]] = (s_ip[i], int(s_port[i]))
        self.__servers_lock.release()
        
        # Print Server list (debug)
        self.__server.output("SERVER LIST")
        for s in self.__servers.keys():
            self.__server.output("%s (%s:%d)" % (s, self.__servers[s][0], self.__servers[s][1]))

        reply = SyncServerListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        return reply


    def _process_SyncClientListMessage(self, msg):
        self.__server.output(("Received ClientList from %s" % msg.serverSrc), logging.INFO)
        c_name = pickle.loads(msg.data)
        c_ip = pickle.loads(msg.clientSrc)
        c_port = pickle.loads(msg.clientDst)
        
        self.__clients_lock.acquire()
        self.__clients.clear()
        
        for i in range(len(c_name)):
            self.__clients[c_name[i]] = (c_ip[i], int(c_port[i]))
        self.__clients_lock.release()
        
        # Print Client list (debug)
        self.__server.output("CLIENT LIST")
        for c in self.__clients.keys():
            self.__server.output("%s (%s:%d)" % (c, self.__clients[c][0], self.__clients[c][1]))
        
        reply = SyncClientListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.serverDst = msg.serverSrc
        return reply
