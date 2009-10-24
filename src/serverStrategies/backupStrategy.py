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
		print "Behaviour: %s" % self.name
		if self.__master != None:
			print "(master: %s)" % self.__master[0]


	def get_master(self):
		return self.__master
	
	
	def elect_new_master(self):
		print 'Electing a new Master...'
		# 1) Elect a new Master
		self.__master = None
		
		while len(self.__servers) > 0:
			# Get a candidate
			curr = self.__servers.iteritems()
			candidate = curr.next()
			print "Candidate: [%s] %s:%d" % (candidate[0], candidate[1][0], candidate[1][1])
		
			# Notify it
			elect_msg = BecomeMasterMessage(priority=1)
			elect_msg.serverSrc = self.__server.get_name()
			elect_msg.serverDst = candidate[0]
			elect_msg.clientSrc = self.__server.ip			# Our IP
			elect_msg.clientDst = str(self.__server.port)	# Our port
			reply = elect_msg.send(candidate[1][0], candidate[1][1])
			
			# If successful, we can break the loop
			if reply != None and reply.type != ErrorMessage:
				self.__master = candidate
				print "New Master is %s (%s:%d)" % (self.__master[0], self.__master[1][0], self.__master[1][1])
				break
			else:
				print "Candidate %s is down" % candidate[0]
				
		# In any case, remove the server from our list
		if len(self.__servers) > 0:
			del self.__servers[candidate[0]]
						
		# If the list is empty, we become the new Master
		if len(self.__servers) == 0 and self.__master == None:
			print 'No more candidates: I am the Master'
			self.__server.set_role(self.__server.MASTER)
			
		# 2) Notify connected Clients
		# TODO
		
		# 3) Notify Idle Servers
		self.__notify_servers()
	
	
	def __notify_servers(self):
	    for s in self.__servers.keys():
			notify = UpdateServerMessage(priority=1)
			notify.serverSrc = self.__server.get_name()
			notify.serverDst = s[0]
			
			if self.__server.get_role() == self.__server.MASTER:
				notify.clientSrc = self.__server.ip			# Our IP
				notify.clientDst = str(self.__server.port)	# Our port
				notify.data = self.__server.get_name()		# Our name
			else:
				notify.clientSrc = self.__master[1][0]		# Master IP
				notify.clientDst = str(self.__master[1][1])	# Master port
				notify.data = self.__master[0]				# Master name
			
			srv = self.__servers[s]
			print "Notifying %s (%s:%d)..." % (s, srv[0], srv[1])
			reply = notify.send(srv[0], srv[1])
			
			if reply == None or reply == ErrorMessage:
				print "Error notifying %s (%s:%d)" % (s, srv[0], srv[1])
	
	
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
		reply.clientSrc = self.__master[1][0]			# Master IP address
		reply.clientDst = str(self.__master[1][1])		# Master Port
		reply.data = self.__master[0]					# Master Name
		return reply
	
	
	def _process_SyncServerList(self, msg):
		print "Received ServerList from %s" % msg.serverSrc
		s_name = pickle.loads(msg.clientSrc)
		s_ip = pickle.loads(msg.clientDst)
		s_port = pickle.loads(msg.data)
		
		for i in range(len(s_name)):
			self.__servers[s_name[i]] = (s_ip[i], int(s_port[i]))
		
		# Print Server List (debug)
		print 'SERVER LIST'
		for s in self.__servers.keys():
			print "[%s] %s:%d" % (s, self.__servers[s][0], self.__servers[s][1])

		reply = SyncServerList(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.serverDst = msg.serverSrc
		return reply


	def _process_SyncClientList(self, msg):
		# TODO
		reply = ErrorMessage(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		reply.data = "Unknown message type: " + msg.type
		return reply
