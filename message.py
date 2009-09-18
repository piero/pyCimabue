'''
Created on 14 Sep 2009

@author: piero
'''

import socket
import pickle
import logging

class Message:

	def __init__(self, socket = None):
		self.type = self.__class__.__name__
		self.clientSrc = ''
		self.clientDst = ''
		self.serverSrc = ''
		self.serverDst = ''
		self.data = ''
		self.skt = socket
		self.use_external_socket = False
		self.MAX_SIZE = 2048
		self.RECV_TIMEOUT = 5
		if self.skt != None:
			self.use_external_socket = True
			print '[#] Message: Using external socket:', str(self.skt.fileno())


	def __str__(self):
		msg = "[" + self.type + "]\n"
		msg = msg + "\tCS: " + self.clientSrc + "\n"
		msg = msg + "\tCD: " + self.clientDst + "\n"
		msg = msg + "\tSS: " + self.serverSrc + "\n"
		msg = msg + "\tSD: " + self.serverDst + "\n"
		msg = msg + "\tD: " + self.data
		return msg


	def msg2dict(self):
		msg_dict = {'t': self.type}
		msg_dict['cs'] = self.clientSrc
		msg_dict['cd'] = self.clientDst
		msg_dict['ss'] = self.serverSrc
		msg_dict['sd'] = self.serverDst
		msg_dict['d'] = self.data
		return msg_dict
	
	
	def dict2msg(self, msg_dict):
		self.type = msg_dict['t']
		self.clientSrc = msg_dict['cs']
		self.clientDst = msg_dict['cd']
		self.serverSrc = msg_dict['ss']
		self.serverDst = msg_dict['sd']
		self.data = msg_dict['d']


	def send(self, dstAddress, dstPort):
		if self.use_external_socket == False:
			try:
				self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.skt.connect((dstAddress, dstPort))
	
			except socket.error, (value, message):
				if self.skt:
					self.skt.close()
				logging.error("[!] Message.send(): Socket error: " + str(message))
				self.type = ErrorMessage
				self.data = str(message)
				return

		line = pickle.dumps(self.msg2dict())
		self.skt.send(line)
		logging.debug("[ ] Sent message: \"" + line + "\"")
		
		# Receive reply
		raw_data = ''
		try:
			self.skt.settimeout(self.RECV_TIMEOUT)
			raw_data = self.skt.recv(self.MAX_SIZE)
		
		except socket.timeout, message:
			if self.skt:
				self.skt.close()
			logging.error("[!] Message.send(): " + str(message))
			self.type = ErrorMessage
			self.data = str(message)
			return
		
		except socket.error, (value, message):
			if self.skt:
				self.skt.close()
			logging.error("[!] Message.send(): " + str(message))
			self.type = ErrorMessage
			self.data = str(message)
			return
		
		self.dict2msg(pickle.loads(raw_data))
		if self.use_external_socket == False:
			self.skt.close()
		return self
		

	def recv(self, sock):
		raw_data = ''

		try:
			raw_data = sock.recv(self.MAX_SIZE)
		
		except socket.error, (value, message):
			if sock:
				sock.close()
			logging.error("[!] Message.recv(): Socket error: " + str(message))
			self.type = ErrorMessage
			self.data = str(message)
			return
		
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