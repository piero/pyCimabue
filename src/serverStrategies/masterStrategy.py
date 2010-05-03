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
        """
        Add a Client and update the Backup accordingly.
        Return the list of other connected Clients as a message.
        """
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
        """Send a message to destination Client"""
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
        """
        Ping Messages are used to determine other nodes' liveness.
        When a Ping Message is received, the corresponding entry must be updated.
        """
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
        """Nothing to document for the moment."""
        self.__server.output("Processing ErrorMessage")
        if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
        
        reply = ErrorMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        return reply
    
    
    def _process_HelloMessage(self, msg):
        """
        Determine role of the sender and return the proper message.
        If there's no Backup, the new Server becomes the Backup.
        Otherwise it's an Idle Server, and Backup is updated accordingly.
        """
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
            reply.data = pickle.dumps(self.__server.clients)    # Client list
        
        else:
            reply = WelcomeIdleMessage(msg.skt, msg.priority)
            reply.clientSrc = self.__server.ip              # Master IP address
            reply.clientDst = str(self.__server.port)       # Master Port
                        
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

        reply.serverSrc = self.__server.get_name()      # Master Name
        reply.serverDst = msg.serverSrc
        return reply
        
    
    def _process_SyncClientListMessage(self, msg):
        """Update the list of connected Clients."""        
        self.__server.clients_lock.acquire()
        self.__server.clients.clear()
        self.__server.clients = pickle.loads(msg.data)
        self.__server.clients_lock.release()
        self.__server.print_client_list()
        
        reply = SyncClientListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        return reply
    
    
    def _process_SyncServerListMessage(self, msg):
        """Update the list of connected Servers."""
        self.__server.servers_lock.acquire()
        self.__server.servers.clear()
        self.__server.servers = pickle.loads(msg.data)
        self.__server.servers_lock.release()
        self.__server.print_server_list()
        
        reply = SyncServerListMessage(msg.skt, msg.priority)
        reply.serverSrc = self.__server.get_name()
        reply.clientDst = msg.clientSrc
        return reply
    

    def sync_server_list(self):
        """Create a list of connected Servers and returns it into a Message."""
        msg = SyncServerListMessage(priority=0, wait_for_reply=False)
        msg.serverSrc = self.__server.get_name()
        msg.serverDst = self.backup[0]
        
        self.__server.servers_lock.acquire()
        msg.data = pickle.dumps(self.__server.servers)
        self.__server.servers_lock.release()
            
        return msg
    
    
    def sync_client_list(self, except_client=None):
        """
        Create a list of connected Clients.
        Notify all Clients other than except_client.
        Return a list with the names of connected Clients.
        """
        c_names = self.__server.get_client_list()[0]

        self.__server.clients_lock.acquire()
        
        # Notify all connected Clients
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
        """Send a message to Backup with the list of connected Clients."""
        if self.backup is not None:            
            self.__server.output("[i] Updating clients on Backup Server %s..." % self.backup[0])
            backup_update = SyncClientListMessage(priority=0)
            backup_update.serverSrc = self.__server.get_name()
            backup_update.serverDst = self.backup[0]
            self.__server.clients_lock.acquire()
            backup_update.data = pickle.dumps(self.__server.clients)
            self.__server.clients_lock.release()
        
            reply = backup_update.send(self.backup[1], self.backup[2])
            if reply is None or reply.type == 'ErrorMessage':
                self.__server.output("[!] Error synchronizing client list on Backup Server")
                self.__server.output(">>> %s" % backup_update.data)


    def __forward_message(self, dest_client, msg):
        """Forward a message to the specified client."""
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
    