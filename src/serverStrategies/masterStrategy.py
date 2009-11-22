'''
Created on 22 Sep 2009

@author: piero
'''

from serverStrategy import *


class MasterStrategy(ServerStrategy):
	
	def __init__(self, server, backup=None):
		self.__server = server
		self.name = self.__server.MASTER
		self.clients = {}			# List of Clients
		self.servers = {}			# List of Servers: (name, (ip, port))
		self.servers_ping = {}		# Servers ping timestamps (name, last_ping_ts)
		self.clients_ping = {}		# Clients ping timestamps (name, last_ping_ts)
		self.backup = backup
		
		self.__server.output("Behaviour: %s" % self.name)
		if backup != None:
			self.__server.output("(backup: %s (%s:%d)" % (self.backup[0], self.backup[1], self.backup[2]))
	
	
	def _process_ConnectMessage(self, msg):
		self.__server.output("Processing ConnectMessage")
		self.clients[msg.clientSrc] = (msg.serverDst, int(msg.data))
		self.__server.output("[+] Added client %s (%s:%d)" % (msg.clientSrc,
															self.clients[msg.clientSrc][0],
															self.clients[msg.clientSrc][1]))
				
		c_names = self.sync_client_list(msg.clientSrc)
		
		reply = SyncClientListMessage(msg.skt, msg.priority)
		reply.clientDst = msg.clientSrc
		reply.serverSrc = self.__server.get_name()
		reply.data = pickle.dumps(c_names)
		return reply
	
	
	def _process_SendMessage(self, msg):
		self.__server.output("Processing SendMessage")
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		if msg.clientDst in self.clients.keys():
			# Forward the message to the destination client
			reply = self.__forward_message(self.clients[msg.clientDst], msg)
			
		else:
			reply = ErrorMessage(msg.skt, msg.priority)
			reply.data = "Destination not found: " + msg.clientDst
		
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		
		# Use the same socket for the reply
		reply.skt = msg.skt
		return reply

	
	def _process_PingMessage(self, msg):
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		# Process Ping messages from other servers
		if msg.serverSrc != None:
			if self.backup != None and msg.serverSrc != self.backup[0] and msg.serverSrc not in self.servers.keys():
				self.__server.output("Received Ping from unknown server %s" % msg.serverSrc)
				return ErrorMessage(msg.skt)
		
			# Update ping list
			self.servers_ping[msg.serverSrc] = time.time()
				
			reply = PingMessage(msg.skt, msg.priority)
			reply.serverSrc = self.__server.get_name()
			reply.serverDst = msg.serverSrc
			return reply
		
		# Process Ping messages from clients
		elif msg.clientSrc != None:
			if msg.clientSrc not in self.clients.keys():
				self.__server.output("Received Ping from unknown client %s" % msg.clientSrc)
				return ErrorMessage(msg.skt)
			
			# Update ping list
			self.clients_ping[msg.clientSrc] = time.time()
			
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
		
		if self.backup == None:
			self.backup = (msg.serverSrc, msg.clientSrc, int(msg.clientDst))
			self.servers_ping[msg.serverSrc] = time.time()
			self.__server.output("Set backup: %s (%s:%d) [%d]" % (self.backup[0],
																self.backup[1],
																self.backup[2],
																self.servers_ping[msg.serverSrc]))
			reply = WelcomeBackupMessage(msg.skt, msg.priority)
		else:
			reply = WelcomeIdleMessage(msg.skt, msg.priority)
			
			# Add new Server
			self.servers[msg.serverSrc] = (msg.clientSrc, int(msg.clientDst))
			self.servers_ping[msg.serverSrc] = time.time()
			s = self.servers[msg.serverSrc]
			self.__server.output("Added: %s (%s:%d) [%d]" % (msg.serverSrc,
															s[0],
															s[1],
															self.servers_ping[msg.serverSrc]))
			# Update Backup Server
			update_msg = self.sync_server_list()
			update_msg.send(self.backup[1], self.backup[2])

		reply.clientSrc = self.__server.ip				# Master IP address
		reply.clientDst = str(self.__server.port)		# Master Port
		reply.data = self.__server.get_name()			# Master Name
		reply.serverSrc = self.__server.get_name()
		reply.serverDst = msg.serverSrc
		return reply
	

	def sync_server_list(self):
		msg = SyncServerListMessage(priority=0)
		msg.serverSrc = self.__server.get_name()
		msg.serverDst = self.backup[0]
		
		s_names = []
		s_ip = []
		s_port = []
		
		for s in self.servers.keys():
			s_names.append(s)
			s_ip.append(self.servers[s][0])
			s_port.append(self.servers[s][1])
			
		msg.clientSrc = pickle.dumps(s_names)
		msg.clientDst = pickle.dumps(s_ip)
		msg.data = pickle.dumps(s_port)
		return msg
	
	
	def sync_client_list(self, client=None):
		c_names = []
		c_ip = []
		c_port = []
		
		for c in self.clients.keys():
			c_names.append(c)
			c_ip.append(self.clients[c][0])
			c_port.append(self.clients[c][1])
		
		if client != None:
			# Notify the other clients
			client_update = SyncClientListMessage(priority=0)
			client_update.serverSrc = self.__server.get_name()
			client_update.data = pickle.dumps(c_names)
			
			for c in self.clients.keys():
				if c != client:
					self.__server.output("[i] Updating clients on %s..." % c)
					client_update.clientDst = c
					
					reply = client_update.send(self.clients[c][0], self.clients[c][1])
					if reply == None or reply.type == ErrorMessage:
						self.__server.output("[!] Error synchronizing client list on %s" % c)
	
		# Notify the Backup Server
		if self.backup != None:
			self.__server.output("[i] Updating clients on Backup Server %s..." % self.backup[0])
			backup_update = SyncClientListMessage(priority=0)
			backup_update.serverSrc = self.__server.get_name()
			backup_update.serverDst = self.backup[0]
			backup_update.clientSrc = pickle.dumps(c_ip)
			backup_update.clientDst = pickle.dumps(c_port)
			backup_update.data = pickle.dumps(c_names)
		
			reply = backup_update.send(self.backup[1], self.backup[2])
			if reply == None or reply.type == ErrorMessage:
				self.__server.output("[!] Error synchronizing client list on Backup Server")
		
		return c_names
	

	def __forward_message(self, dest_client, msg):
		self.__server.output(">>> Forwarding to %s (%s:%d)" % (msg.clientSrc, dest_client[0], dest_client[1]))
		
		fwd_msg = SendMessage()
		fwd_msg.clientSrc = msg.clientSrc
		fwd_msg.clientDst = msg.clientDst
		fwd_msg.serverSrc = self.__server.get_name()
		fwd_msg.data = msg.data

		reply = fwd_msg.send(dest_client[0], dest_client[1])
		
		if reply == None:
			return fwd_msg
		else:
			return reply
	