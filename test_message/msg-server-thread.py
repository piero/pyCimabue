#!/usr/bin/env python

from message import *
import select
import sys
import threading


class Server:

	def __init__(self):
		self.HOST = ''
		self.PORT = 50000
		self.backlog = 5
		self.size = 1024
		self.server = None
		self.threads = []
		
	def open_socket(self):
		try:
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server.bind((self.HOST, self.PORT))
			self.server.listen(self.backlog)
			
		except socket.error, (value, message):
			if self.server:
				self.server.close()
			print "Couldn't open socket: " + message
			sys.exit(1)
			
	def run(self):
		self.open_socket()
		input = [self.server, sys.stdin]
		running = 1
		
		while running:
			inputready, outputready, exceptready = select.select(input, [], [])
			
			for s in inputready:
			
				if s == self.server:
					# Handle the server socket
					c = ClientProxy(self.server.accept())
					c.start()
					self.threads.append(c)
					
				elif s == sys.stdin:
					# Handle stdin
					junk = sys.stdin.readline()
					running = 0
					
		# Close all threads
		self.server.close()
		for c in self.threads:
			c.join()


class ClientProxy(threading.Thread):

	def __init__(self, (client, address)):
		threading.Thread.__init__(self)
		self.client = client
		self.address = address
		self.size = 1024
		print 'Client:', address
		
	def run(self):
		#print 'Running thread', self.ident
		running = 1
		
		while running:
		
			data = self.client.recv(self.size)	
			if data:
				msg = Message()
				msg_dict = pickle.loads(data)
				msg.dict2msg(msg_dict)
				print 'Received:', str(msg)
				
				if msg.type == 'ConnectMessage':
					print 'CONNECT MESSAGE'
				elif msg.type == 'SendMessage':
					print 'SEND MESSAGE'
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
				msg.reply(self.client)

			self.client.close()
			running = 0
			
		#print 'Exit thread', self.ident, '\n'
		

if __name__ == "__main__":
	s = Server()
	s.run()
	print '[exit]\n'

