from message import *
import threading
import sys

class ClientProxy(threading.Thread):

	def __init__(self, server, socket, address):
		threading.Thread.__init__(self)
		self.server = server
		self.socket = socket
		self.address = address
		self.name = ''
		self.size = 1024
		self.connected = False
		self.running = False
		
	def run(self):
		self.running = True
		
		while self.running:
			try:
				data = self.socket.recv(self.size)
				
			except socket.error, (value, message):
				if self.socket:
					self.socket.close()
				#logging.error("Socket error: " + str(message))
				if self.connected:
					self.connected = False
					self.server.remClient(self)
				self.running = False
				break
				
			if data:
				msg = Message(self.socket)
				msg_dict = pickle.loads(data)
				msg.dict2msg(msg_dict)
				print 'Received:', str(msg)
				
				if msg.type == 'ConnectMessage':
					print 'CONNECT MESSAGE'
					self.name = msg.clientSrc
					self.server.addClient(self)
					self.connected = True
				
				elif msg.type == 'SendMessage':
					print 'SEND MESSAGE'
					destClient = self.server.getClient(msg.clientDst)
					if destClient != None:
						# TODO TODO TODO
						pass
					else:
						reply = ErrorMessage()
						reply.clientDst = msg.clientSrc
						reply.serverSrc = self.server.name
						reply.reply(self.socket)
						break
				
				elif msg.type == 'AddClientMessage':
					print 'ADD CLIENT MESSAGE'
				
				elif msg.type == 'PingMessage':
					print 'PING MESSAGE'
				
				else:
					print 'UNKNOWN MESSAGE'
				
				# Reply
				msg.clientDst = msg.clientSrc
				msg.clientSrc = ''
				msg.serverSrc = msg.serverDst
				msg.serverDst = ''
				msg.reply(self.socket)			
