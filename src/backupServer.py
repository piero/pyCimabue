'''
Created on 22 Sep 2009

@author: piero
'''

from slavePingAgent import *
from message import *


class BackupServer:
	
	def __init__(self, server):
		self.__server = server
		self.__master = (None, None, None)
		self.__servers = {}
		self.__clients = {}
		self.__ping_agent = SlavePingAgent(self)
		print 'Behaviour:', self.__server.BACKUP
		
		
	def quit(self):
		if self.__ping_agent.isAlive():
			print "[x] Quitting Ping Agent..."
			self.__ping_agent.quit()
			self.__ping_agent.join(2.0)

		
		
	def set_master(self, master):
		self.__master = master
		self.__ping_agent.start()
		print "Set master: %s (%s:%d)" % (self.__master[0], self.__master[1], self.__master[2])
		
		
	def get_master(self):
		return self.__master
	
	
	def get_server_name(self):
		return self.__server.get_name()
		
	
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
		reply.clientSrc = self.__master[1]			# Master IP address
		reply.clientDst = str(self.__master[2])		# Master Port
		reply.data = self.__master[0]				# Master Name
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
