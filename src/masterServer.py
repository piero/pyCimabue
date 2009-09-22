'''
Created on 22 Sep 2009

@author: piero
'''

from message import *


class MasterServer:
	
	def __init__(self, server):
		self.__server = server
		self.__clients = {}		# List of Clients
		self.__servers = {}		# List of Servers
		self.__backup = None
		print 'Behaviour:', self.__server.MASTER
		
	
	def _process_ConnectMessage(self, msg):
		print 'Processing ConnectMessage'
		self.__clients[msg.clientSrc] = msg.data
		print '[+] Added: %s: %s' % (msg.clientSrc, str(self.__clients[msg.clientSrc]))
		reply = ConnectMessage(msg.skt, msg.priority)
		reply.clientDst = msg.clientSrc
		reply.serverSrc = self.__server.get_name()
		return reply
	
	
	def _process_SendMessage(self, msg):
		print 'Processing SendMessage'
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		if msg.clientDst in self.__clients.keys():
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
		print 'Processing PingMessage'
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		reply = PingMessage(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		return reply
		
	
	def _process_ErrorMessage(self, msg):
		print 'Processing ErrorMessage'
		if not self.__server._check_recipient(msg): return ErrorMessage(msg.skt)
		
		reply = ErrorMessage(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		return reply
	
	
	def _process_HelloMessage(self, msg):
		print 'Processing HelloMessage'
		
		if self.__backup == None:
			self.__backup = (msg.serverSrc, msg.clientSrc, int(msg.clientDst))
			print 'Set backup: %s (%s:%d)' % (self.__backup[0],  self.__backup[1], self.__backup[2])
			reply = WelcomeBackup(msg.skt, msg.priority)
		else:
			reply = WelcomeIdle(msg.skt, msg.priority)
		
		self.__servers[msg.serverSrc] = (msg.clientSrc, int(msg.clientDst))
		self.__print_server_list()

		reply.clientSrc = self.__server.ip			# Master IP address
		reply.clientDst = str(self.__server.port)		# Master Port
		reply.data = self.__server.get_name()			# Master Name
		reply.serverSrc = self.__server.get_name()
		reply.serverDst = msg.serverSrc
		return reply
	
	
	def __print_server_list(self):
		for s in self.__servers.keys():
			print "[%s] %s:%d" % (s, self.__servers[s][0], self.__servers[s][1]) 