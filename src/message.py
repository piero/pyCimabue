'''
Created on 14 Sep 2009

@author: piero
'''

import socket
import pickle
import logging
from utilities.nullHandler import *

class Message:

	def __init__(self, use_socket = None, priority = 2, wait_for_reply = True):
		self.type = self.__class__.__name__
		self.priority = priority
		self.clientSrc = ""
		self.clientDst = ""
		self.serverSrc = ""
		self.serverDst = ""
		self.data = ""
		self.skt = use_socket
		self.__wait_for_reply = wait_for_reply
		self.__use_external_socket = False
		self.__MAX_SIZE = 2048
		self.__RECV_TIMEOUT = 5

		# Logging
		logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
		self.logger = logging.getLogger('ActiveObject')
		self.logger.setLevel(logging.DEBUG)
		h = NullHandler()
		self.logger.addHandler(h)
		
		if self.skt != None:
			self.__use_external_socket = True
			#self.logger.debug("[%s] Using external socket: %d" % (self.type, self.skt.fileno()))
	
	
	def __del__(self):
		if self.__use_external_socket == False and self.skt != None:
			#self.logger.debug("[MSG] Closing internal socket")
			self.skt.close()
	

	def __str__(self):
		msg = "[" + self.type + "]\n"
		msg = msg + "\tP: " + str(self.priority) + "\n"
		msg = msg + "\tCS: " + self.clientSrc + "\n"
		msg = msg + "\tCD: " + self.clientDst + "\n"
		msg = msg + "\tSS: " + self.serverSrc + "\n"
		msg = msg + "\tSD: " + self.serverDst + "\n"
		msg = msg + "\tD: " + self.data + "\n"
		msg = msg + "\tRP: " + str(self.__wait_for_reply)
		return msg


	def wait_for_reply(self):
		return self.__wait_for_reply


	def msg2dict(self):
		msg_dict = {"t": self.type}
		msg_dict["p"] = self.priority
		msg_dict["cs"] = self.clientSrc
		msg_dict["cd"] = self.clientDst
		msg_dict["ss"] = self.serverSrc
		msg_dict["sd"] = self.serverDst
		msg_dict["d"] = self.data
		msg_dict["rp"] = str(self.__wait_for_reply)
		return msg_dict
	
	
	def dict2msg(self, msg_dict):
		self.type = msg_dict["t"]
		self.priority = msg_dict["p"]
		self.clientSrc = msg_dict["cs"]
		self.clientDst = msg_dict["cd"]
		self.serverSrc = msg_dict["ss"]
		self.serverDst = msg_dict["sd"]
		self.data = msg_dict["d"]
		if msg_dict["rp"] == "True":
			self.__wait_for_reply = True
		else:
			self.__wait_for_reply = False


	def send(self, dstAddress = None, dstPort = None):
		if self.__use_external_socket == False:
			try:
				#self.logger.debug("[MSG] Creating internal socket")
				self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.skt.connect((dstAddress, dstPort))
	
			except socket.error, (value, message):
				if self.skt:
					self.skt.close()
				self.logger.error("[!] Message.send(%s:%d): Socket error: %s" % (dstAddress, dstPort, str(message)))
				self.type = ErrorMessage
				self.data = str(message)
				return None

		line = pickle.dumps(self.msg2dict())
		self.skt.send(line)
		#self.logger.debug("[ ] Sent: " + str(self))
		
		if self.__wait_for_reply:
			# Receive reply
			raw_data = ''
			try:
				self.skt.settimeout(self.__RECV_TIMEOUT)
				raw_data = self.skt.recv(self.__MAX_SIZE)
			
			except socket.timeout, message:
				if self.skt:
					self.skt.close()
				self.logger.error("[!] Message.send(%s:%d): %s" % (dstAddress, dstPort, str(message)))
				self.type = ErrorMessage
				self.data = str(message)
				return None
			
			except socket.error, (value, message):
				if self.skt:
					self.skt.close()
				self.logger.error("[!] Message.send(%s:%d): %s" % (dstAddress, dstPort, str(message)))
				self.type = ErrorMessage
				self.data = str(message)
				return None
			
			self.dict2msg(pickle.loads(raw_data))
			if self.__use_external_socket == False:
				self.skt.close()
			return self
		

	def recv(self, sock):
		raw_data = ''

		try:
			raw_data = sock.recv(self.__MAX_SIZE)
		
		except socket.error, (value, message):
			if sock:
				sock.close()
			self.logger.error("[!] Message.recv(): Socket error: " + str(message))
			self.type = ErrorMessage
			self.data = str(message)
			return None
		
		msg_dict = pickle.loads(raw_data)
		self.dict2msg(msg_dict)


	def reply(self, skt):
		if skt:
			#self.logger.debug("[%s] Replying on socket %d" % (self.type, skt.fileno()))
			line = pickle.dumps(self.msg2dict())
			skt.send(line)
			#self.logger.debug("[ ] Replied: " + str(self))
		else:
			return None


# Subclasses (message types)

class ConnectMessage(Message):
	pass
	
class SendMessage(Message):
	pass

class AddClientMessage(Message):
	pass

class PingMessage(Message):
	pass

class ErrorMessage(Message):
	pass

# Server registration
class HelloMessage(Message):
	pass

class WelcomeBackupMessage(Message):
	pass

class WelcomeIdleMessage(Message):
	pass

# Server synchronization
class SyncServerListMessage(Message):
	pass

class SyncClientListMessage(Message):
	pass

# Server update
class BecomeMasterMessage(Message):
	pass

class BecomeBackupMessage(Message):
	pass

class UpdateServerMessage(Message):
	pass
