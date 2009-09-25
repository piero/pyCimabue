'''
Created on 22 Sep 2009

@author: piero
'''

from message import *


class BackupServer:
	
	def __init__(self, server):
		self.__server = server
		self.__master = (None, None, None)
		self.__servers = {}
		self.__clients = {}
		print 'Behaviour:', self.__server.BACKUP
		
		
	def quit(self):
		pass
		
		
	def set_master(self, master):
		self.__master = master
		print "Set master: %s (%s:%d)" % (self.__master[0], self.__master[1], self.__master[2])
		
	
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
		reply.clientSrc = self.__master[1]	# Master IP address
		reply.clientDst = str(self.__master[2])	# Master Port
		reply.data = self.__master[0]		# Master Name
		return reply
	
	def _process_SyncServerList(self, msg):
		print "Received ServerList from %s" % msg.serverSrc
		s_name = pickle.loads(msg.clientSrc)
		s_ip = pickle.loads(msg.clientDst)
		s_port = pickle.loads(msg.data)
		
		for i in range(len(s_name)):
			print "%d) %s %s:%d" % (i, s_name[i], s_ip[i], s_port[i])
			self.__servers[s_name[i]] = (s_ip[i], int(s_port[i]))
			
		for s in self.__servers.keys():
			print "%s - %s:%d" % (s, (self.__servers[s])[0], (self.__servers[s])[1])
		# TODO
#		reply = ErrorMessage(msg.skt, msg.priority)
#		reply.serverSrc = self.__server.get_name()
#		reply.clientDst = msg.clientSrc
#		reply.data = "Unknown message type: " + msg.type
#		return reply
	
	def _process_SyncClientList(self, msg):
		# TODO
		reply = ErrorMessage(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		reply.data = "Unknown message type: " + msg.type
		return reply
