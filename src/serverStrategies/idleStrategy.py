'''
Created on 22 Sep 2009

@author: piero
'''

from serverStrategy import *


class IdleStrategy(ServerStrategy):
	
	def __init__(self, server, master=None):
		self.__server = server
		self.name = self.__server.IDLE
		self.__master = master
		print "Behaviour: %s" % self.name
		if self.__master != None:
			print "(master: %s)" % self.__master[0]

		
	def get_master(self):
		return self.__master
		
	
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
		# TODO
		reply = ErrorMessage(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		reply.data = "Unknown message type: " + msg.type
		return reply
	
	
	def _process_BecomeMasterMessage(self, msg):
		new_backup = (msg.serverSrc, (msg.clientSrc, int(msg.clientDst)))
		print "Becoming Master (backup: %s (%s:%d)" % (new_backup[0], new_backup[1][0], new_backup[1][1])
		self.__server.set_role(self.__server.MASTER, new_backup)
		
		reply = Message(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		reply.data = ""
		return reply
	
	
	def _process_UpdateServerMessage(self, msg):
		new_master = (msg.data, (msg.clientSrc, int(msg.clientDst)))
		print "Updating Master: %s (%s:%d)" % (new_master[0], new_master[1][0], new_master[1][1])
		self.__master = new_master
		
		reply = Message(msg.skt, msg.priority)
		reply.serverSrc = self.__server.get_name()
		reply.clientDst = msg.clientSrc
		reply.data = ""
		return reply
