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
		reply = Message(msg.skt, msg.priority)
		reply.clientDst = msg.clientSrc
		reply.serverSrc = self.__server.get_name()
		return reply
	
	
	def _process_SendMessage(self, msg):
		self.__server.output("Processing SendMessage")
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		if msg.clientDst in self.clients.keys():
			# TODO: Send message to client
			#client = self.__clients[msg.clientDst]
			reply = SendMessage(msg.skt, msg.priority)			
		else:
			reply = ErrorMessage(msg.skt, msg.priority)
			reply.data = "Destination not found: " + msg.clientDst
		
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		return reply

	
	def _process_PingMessage(self, msg):
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		if msg.serverSrc != self.backup[0] and self.servers.get(msg.serverSrc) == None:
			self.__server.output("Received Ping from unknown %s" % msg.serverSrc)
			return ErrorMessage(msg.skt)
		
		# Update ping list
		self.servers_ping[msg.serverSrc] = time.time()
		#print "Updated: %s: %d" % (msg.serverSrc, self.servers_ping[msg.serverSrc])
			
		reply = PingMessage(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		return reply
		
	
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
			reply = WelcomeBackup(msg.skt, msg.priority)
		else:
			reply = WelcomeIdle(msg.skt, msg.priority)
			
			# Add new Server
			self.servers[msg.serverSrc] = (msg.clientSrc, int(msg.clientDst))
			self.servers_ping[msg.serverSrc] = time.time()
			s = self.servers[msg.serverSrc]
			self.__server.output("Added: %s (%s:%d) [%d]" % (msg.serverSrc,
															s[0],
															s[1],
															self.servers_ping[msg.serverSrc]))
			self.sync_server_list()	

		reply.clientSrc = self.__server.ip				# Master IP address
		reply.clientDst = str(self.__server.port)		# Master Port
		reply.data = self.__server.get_name()			# Master Name
		reply.serverSrc = self.__server.get_name()
		reply.serverDst = msg.serverSrc
		return reply
	

	def sync_server_list(self):
		msg = SyncServerList(priority=0)
		msg.serverSrc = self.__server.get_name()
		msg.serverDst = self.backup[0]
		
		s_names = []
		s_ip = []
		s_port = []
		
		for s in self.servers.keys():
			s_names.append(s)
			s_ip.append((self.servers[s])[0])
			s_port.append((self.servers[s])[1])
			
		msg.clientSrc = pickle.dumps(s_names)
		msg.clientDst = pickle.dumps(s_ip)
		msg.data = pickle.dumps(s_port)
		msg.send(self.backup[1], self.backup[2])
