from message import *
from listener import *
from executer import *
from Queue import *
import threading
import sys

class ServerProxy:

	def __init__(self, host, port, caller):
		self.server_ip = host
		self.server_port = port
		self.client = caller
		self.connected = False	# Are we connected to a Server?
		self.server = ''		# Initialized when self.connected == True
		self.msg_queue = Queue()
		self.listener = Listener(self.client, self)
		self.executer = Executer(self.client, self)

	
	def connect(self):
		try:
			self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.skt.connect((self.server_ip, self.server_port))
		except socket.error, (value, message):
			if self.skt:
				self.skt.close()
			logging.error("[!] Message.send(): Socket error: " + str(message))
			self.type = ErrorMessage
			self.data = str(message)
			return

		msg = ConnectMessage(self.skt)
		msg.clientSrc = self.client.name
		msg.data = str(self.client.client_port)
		reply = msg.send(self.server_ip, self.server_port)

		if msg.type != ErrorMessage:
			self.connected = True
			self.server = msg.serverSrc
			print 'Set Server:', self.server

			self.listener.start()
			self.executer.start()
		else:
			self.print_error(msg.data)
		return msg

		
	def sendMessage(self, dest, message):
		msg = SendMessage(self.skt)
		msg.clientSrc = self.client.name
		msg.clientDst = dest
		msg.serverDst = self.server
		msg.data = message
		msg.send(self.server_ip, self.server_port)
		if msg.type == ErrorMessage:
			self.print_error(msg.data)
		return msg

		
	def quit(self):
		self.skt.close()
		
		if self.executer.is_alive():
			print '[x] Stopping executer...'
			self.msg_queue.put(None)
			self.executer.join()
	
		if self.listener.is_alive():
			print '[x] Stopping listener...'
			self.listener.running = False
			self.listener.join()

	def print_error(self, message):
		print '[', self.__class__.__name__, '] Error:', message
		


