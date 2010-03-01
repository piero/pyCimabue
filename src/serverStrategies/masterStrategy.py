'''
Created on 22 Sep 2009

@author: piero
'''

from serverStrategy import *


class MasterStrategy(ServerStrategy):
    
    def __init__(self, server, backup=None):
        self.__server = server
        self.name = self.__server.MASTER
        self.backup = backup
        
        self.__server.output("Behaviour: %s" % self.name)
        if backup is not None:
            self.__server.output("(backup: %s (%s:%d)" % (self.backup[0], self.backup[1], self.backup[2]))
    
    
    def _process_ConnectMessage(self, msg):
        self.__server.output("Processing ConnectMessage")
        self.__server.clients_lock.acquire()
        self.__server.clients[msg.clientSrc] = (msg.serverDst, int(msg.data))
        self.__server.clients_ping[msg.clientSrc] = time.time()
        self.__server.clients_lock.release()
        self.__server.output("[+] Added client %s (%s:%d)" % (msg.clientSrc,
                                                            self.__server.clients[msg.clientSrc][0],
                                                            self.__server.clients[msg.clientSrc][1]))
                
        c_names = self.sync_client_list(except_client=msg.clientSrc)
        
        if self.backup is not None:
            # Schedule an update of Backup's client list
            task = Message(priority=0)
            task.data = 'sync_backup_client_list'
            self.__server.add_request(task, self.__server.LOCAL_REQUEST)
        
        reply = SyncClientListMessage(msg.skt, msg.priority)
        reply.clientDst = msg.clientSrc
        reply.serverSrc = self.__server.get_name()
        reply.data = pickle.dumps(c_names)
        return reply
    
    
    def _process_SendMessage(self, msg):
        self.__server.output("Processing SendMessage")
        if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
        
        self.__server.clients_lock.acquire()
        if msg.clientDst in self.__server.clients.keys():
            # Forward the message to the destination client
            reply = self.__forward_message(self.__server.clients[msg.clientDst], msg)
        else:
            reply = ErrorMessage(msg.skt, msg.priority)
            reply.data = "Destination not found: " + msg.clientDst
        self.__server.clients_lock.release()
        
        if reply is None:
            reply = ErrorMessage(priority=msg.priority)
            reply.data = "Error sending message"
        
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        reply.skt = msg.skt     # Reuse the socket
        return reply

    
    def _process_PingMessage(self, msg):
        if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
        
        # Process Ping messages from other servers
        if msg.serverSrc != "":
            if self.backup is not None and \
            msg.serverSrc != self.backup[0] and \
            msg.serverSrc not in self.__server.servers.keys():
                self.__server.output("Received Ping from unknown server %s" % msg.serverSrc)
                
                # Print Server list (debug)
                self.__server.output("--> SERVER LIST")
                for s in self.__server.servers.keys():
                    self.__server.output("* %s (%s:%d)" % (s, self.__server.servers[s][0], self.__server.servers[s][1]))
                
                return ErrorMessage(msg.skt)
            
            # Update ping list
            self.__server.servers_lock.acquire()
            self.__server.servers_ping[msg.serverSrc] = time.time()
            self.__server.servers_lock.release()
                
            reply = PingMessage(msg.skt, msg.priority)
            reply.serverSrc = self.__server.get_name()
            reply.serverDst = msg.serverSrc
            return reply
        
        # Process Ping messages from clients
        elif msg.clientSrc != "":
            if msg.clientSrc not in self.__server.clients.keys():
                self.__server.output("Received Ping from unknown client %s" % msg.clientSrc)
                return ErrorMessage(msg.skt)
            
            # Update ping list
            self.__server.clients_lock.acquire()
            self.__server.clients_ping[msg.clientSrc] = time.time()
            self.__server.clients_lock.release()
            
            reply = PingMessage(msg.skt, msg.priority)
            reply.serverSrc = self.__server.get_name()
            reply.clientDst = msg.clientSrc
            return reply
        
        else: return ErrorMessage(msg.skt)
    
    
    def _process_ErrorMessage(self, msg):
        self.__server.output("Processing ErrorMessage")
        if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
        
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        return reply
    
    
    def _process_HelloMessage(self, msg):
        self.__server.output("Processing HelloMessage")
        
        if self.backup is None:
            self.__server.servers_lock.acquire()
            self.backup = (msg.serverSrc, msg.clientSrc, int(msg.clientDst))
            self.__server.servers_ping[msg.serverSrc] = time.time()
            self.__server.servers_lock.release()
            
            self.__server.output("Set backup: %s (%s:%d) [%d]" % (self.backup[0],
                                                                self.backup[1],
                                                                self.backup[2],
                                                                self.__server.servers_ping[msg.serverSrc]))
            reply = WelcomeBackupMessage(msg.skt, msg.priority)
        
        else:
            reply = WelcomeIdleMessage(msg.skt, msg.priority)
            
            # Add new Server
            self.__server.servers_lock.acquire()
            self.__server.servers[msg.serverSrc] = (msg.clientSrc, int(msg.clientDst))
            self.__server.servers_ping[msg.serverSrc] = time.time()
            s = self.__server.servers[msg.serverSrc]
            self.__server.servers_lock.release()
            
            self.__server.output("Added: %s (%s:%d) [%d]" % (msg.serverSrc,
                                                            s[0],
                                                            s[1],
                                                            self.__server.servers_ping[msg.serverSrc]))
            # Update Backup Server
            update_msg = self.sync_server_list()
            update_msg.send(self.backup[1], self.backup[2])

        reply.clientSrc = self.__server.ip                # Master IP address
        reply.clientDst = str(self.__server.port)        # Master Port
        reply.serverSrc = self.__server.get_name()        # Master Name
        reply.serverDst = msg.serverSrc
        return reply
        
    
    def _process_SyncClientListMessage(self, msg):
        c_name = pickle.loads(msg.data)
        c_ip = pickle.loads(msg.clientSrc)
        c_port = pickle.loads(msg.clientDst)
        
        self.__server.clients_lock.acquire()
        self.__server.clients.clear()
        
        for i in range(len(c_name)):
            self.__server.clients[c_name[i]] = (c_ip[i], int(c_port[i]))
        self.__server.clients_lock.release()
        
        reply = SyncClientListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        return reply
    
    
    def _process_SyncServerListMessage(self, msg):
        s_name = pickle.loads(msg.data)
        s_ip = pickle.loads(msg.clientSrc)
        s_port = pickle.loads(msg.clientDst)
        
        self.__server.servers_lock.acquire()
        self.__server.servers.clear()
        
        for i in range(len(s_name)):
            self.__server.servers[s_name[i]] = (s_ip[i], int(s_port[i]))
        self.__server.servers_lock.release()
        
        reply = SyncServerListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        return reply
    

    def sync_server_list(self):
        msg = SyncServerListMessage(priority=0, wait_for_reply=False)
        msg.serverSrc = self.__server.get_name()
        msg.serverDst = self.backup[0]
        
        s_names = []
        s_ip = []
        s_port = []
        
        self.__server.servers_lock.acquire()
        for s in self.__server.servers.keys():
            s_names.append(s)
            s_ip.append(self.__server.servers[s][0])
            s_port.append(self.__server.servers[s][1])
        self.__server.servers_lock.release()
            
        msg.clientSrc = pickle.dumps(s_names)
        msg.clientDst = pickle.dumps(s_ip)
        msg.data = pickle.dumps(s_port)
        return msg
    
    
    def sync_client_list(self, except_client=None):
        c_names = []
        c_ip = []
        c_port = []
        
        # Make the clients' list
        self.__server.clients_lock.acquire()
        for c in self.__server.clients.keys():
            c_names.append(c)
            c_ip.append(self.__server.clients[c][0])
            c_port.append(self.__server.clients[c][1])
        
        # Notify the clients
        for c in self.__server.clients.keys():
            if c != except_client:
                self.__server.output("[i] Updating %s's client list..." % c)
                client_update = SyncClientListMessage(priority=0)
                client_update.serverSrc = self.__server.get_name()
                client_update.data = pickle.dumps(c_names)
                client_update.clientDst = c
                
                reply = client_update.send(self.__server.clients[c][0], self.__server.clients[c][1])
                if reply is None or reply.type != 'SyncClientListMessage':
                    self.__server.output("[!] Error synchronizing client list on %s" % c)
                    self.__server.output(">>> %s" % client_update.data)
        self.__server.clients_lock.release()
        return c_names
    
    def sync_backup_client_list(self):
        if self.backup is not None:
            c_names = []
            c_ip = []
            c_port = []
            
            self.__server.clients_lock.acquire()
            for c in self.__server.clients.keys():
                c_names.append(c)
                c_ip.append(self.__server.clients[c][0])
                c_port.append(self.__server.clients[c][1])
            self.__server.clients_lock.release()
            
            self.__server.output("[i] Updating clients on Backup Server %s..." % self.backup[0])
            backup_update = SyncClientListMessage(priority=0)
            backup_update.serverSrc = self.__server.get_name()
            backup_update.serverDst = self.backup[0]
            backup_update.clientSrc = pickle.dumps(c_ip)
            backup_update.clientDst = pickle.dumps(c_port)
            backup_update.data = pickle.dumps(c_names)
        
            reply = backup_update.send(self.backup[1], self.backup[2])
            if reply is None or reply.type == 'ErrorMessage':
                self.__server.output("[!] Error synchronizing client list on Backup Server")
                self.__server.output(">>> %s" % backup_update.data)


    def __forward_message(self, dest_client, msg):
        self.__server.output(">>> Forwarding to %s (%s:%d)" % (msg.clientSrc,
                                                               dest_client[0],
                                                               dest_client[1]),
                                                               logging.DEBUG)
        
        fwd_msg = SendMessage()
        fwd_msg.clientSrc = msg.clientSrc
        fwd_msg.clientDst = msg.clientDst
        fwd_msg.serverSrc = self.__server.get_name()
        fwd_msg.data = msg.data

        reply = fwd_msg.send(dest_client[0], dest_client[1])
        
        if reply is None or reply.type == 'ErrorMessage':
            self.__server.output("Couldn't forward message to %s (%s:%d)" % (msg.clientDst,
                                                                             dest_client[0],
                                                                             dest_client[1]),
                                                                             logging.ERROR)    
        return reply
    