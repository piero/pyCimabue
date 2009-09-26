'''
Created on 14 Sep 2009

@author: piero
'''

import socket
import pickle
import logging

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
		if self.skt != None:
			self.__use_external_socket = True
			logging.debug("Message: Using external socket:" + str(self.skt.fileno()))
		

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
				self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.skt.connect((dstAddress, dstPort))
	
			except socket.error, (value, message):
				if self.skt:
					self.skt.close()
				logging.error("[!] Message.send(): Socket error: " + str(message))
				self.type = ErrorMessage
				self.data = str(message)
				return None

		line = pickle.dumps(self.msg2dict())
		self.skt.send(line)
		logging.debug("[ ] Sent message: \"" + line + "\"")
		
		if self.__wait_for_reply:
			# Receive reply
			raw_data = ''
			try:
				self.skt.settimeout(self.__RECV_TIMEOUT)
				raw_data = self.skt.recv(self.__MAX_SIZE)
			
			except socket.timeout, message:
				if self.skt:
					self.skt.close()
				logging.error("[!] Message.send(): " + str(message))
				self.type = ErrorMessage
				self.data = str(message)
				return None
			
			except socket.error, (value, message):
				if self.skt:
					self.skt.close()
				logging.error("[!] Message.send(): " + str(message))
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
			logging.error("[!] Message.recv(): Socket error: " + str(message))
			self.type = ErrorMessage
			self.data = str(message)
			return None
		
		msg_dict = pickle.loads(raw_data)
		self.dict2msg(msg_dict)


	def reply(self, skt):
		print 'Message: Replying on socket', str(skt.fileno())
		line = pickle.dumps(self.msg2dict())
		skt.send(line)
		logging.debug("[ ] Replied to message: \"" + line + "\"")


# Subclasses

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

class WelcomeBackup(Message):
	pass

class WelcomeIdle(Message):
	pass

# Server synchronization
class SyncServerList(Message):
	pass

class SyncClientList(Message):
	pass
