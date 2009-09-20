#!/usr/bin/env python

from clientProxy import *
import select
import socket
import sys
import time


class Server:

	def __init__(self, host = 'localhost', port = 50000):
		self.name = str(int(time.time() * 1000))
		self.HOST = host
		self.PORT = port
		self.backlog = 5
		self.size = 1024
		self.SELECT_TIMEOUT = 1.0
		self.clients = {}
		print '[ ] Server:', self.name

	def run(self):
		try:
			server_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			server_skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			server_skt.bind((self.HOST, self.PORT))
			print 'Listening on port', self.PORT, '...'
			server_skt.listen(self.backlog)

		except socket.error, (value, message):
			if server_skt:
				server_skt.close()
			print 'Couldn\'t open socket:', message
			sys.exit(1)

		input = [server_skt, sys.stdin]
		running = 1

		while running:
			inputready, outputready, exceptready = select.select(input,
																 [],
																 [],
																 self.SELECT_TIMEOUT)

			for s in inputready:
	
				if s == server_skt:
					# Handle server socket
					client_skt, address = s.accept()
					print 'New connection from', address
					input.append(client_skt)
			
				elif s == sys.stdin:
					# Handle stdin: exit
					junk = sys.stdin.readline()
					running = 0
			
				else:
					# Handle a client socket
					client = ClientProxy(self, s, address[0])
					client.start()

		# Exit
		server_skt.close()
		for c in self.clients:
			print 'client', c, '...'
			if self.clients[c].is_alive():
				print '[x] Killing client', c, '...'
				self.clients[c].running = False
				self.clients[c].socket.close()
				self.clients[c].join()

	
	def addClient(self, client):
		if client.name not in self.clients:
			self.clients[client.name] = client
			print '[+]', client.name, ':', self.clients[client.name]
		else:
			print '[!]', client.name, 'already exists'
		
	def remClient(self, client):
		if name in self.clients:
			del self.clients[name]
			print '[-]', name, ':', len(self.clients), 'clients left'
		else:
			print '[!]', name, 'not found'
			
	def getClient(self, name):
		if name in self.clients:
			return self.clients[name]
		else:
			return None


# Execution starts here
if __name__ == "__main__":
	s = Server()
	s.run()
	print '[exit]\n'

