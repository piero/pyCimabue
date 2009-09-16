from message import *
import threading

class ServerProxy(threading.Thread):

	def __init__(self, host, port, caller):
		self.host = host
		self.port = port
		self.client = caller
		self.server = ''
		self.connected = False

	
	def run(self):
		pass

	
	def connect(self):
		msg = ConnectMessage()
		msg.clientSrc = self.client
		msg.send(self.host, self.port)
		if msg.type != ErrorMessage:
			self.connected = True
		else:
			self.print_error(msg.data)
		return msg

		
	def sendMessage(self, message):
		msg = SendMessage()
		msg.clientSrc = self.client
		msg.serverDst = self.server
		msg.data = message
		msg.send(self.host, self.port)
		if msg.type == ErrorMessage:
			self.print_error(msg.data)
		return msg


	def print_error(self, message):
		print '[', self.__class__.__name__, '] Error:', message
