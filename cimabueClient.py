#!/usr/bin/env python

from serverProxy import *
from observer import *
import time
import sys


class Client:

	def __init__(self, client_ip = 'localhost', server_ip = 'localhost', client_port = 55000, server_port = 50000):
		self.name = str(int(time.time() * 1000))
		self.client_ip = client_ip
		self.client_port = client_port
		self.server_ip = server_ip
		self.server_port = server_port
		print '[ ] Client: ', self.name

	def run(self):
		# Connect to the Server
		server = ServerProxy(host = self.server_ip, port = self.server_port, caller = self)
		reply = None
		reply = server.connect()
	
		if reply == None or reply.type == ErrorMessage:
			print '[!] Error connecting to server (', self.server_ip, ':', self.server_port, ')'
			print reply.data
			return

		# Wait for input
		while 1:
			# Destination
			sys.stdout.write('to: ')
			dest = sys.stdin.readline()
			if dest == '\n':
				server.quit()
				break
			
			# Message
			sys.stdout.write('msg: ')
			msg = sys.stdin.readline()
			if msg == '\n':
				server.quit()
				break
	
			reply = server.sendMessage(dest, msg)
			print 'Got reply:', reply


# Execution starts here
if __name__ == "__main__":
	client = Client()
	client.run()
	print '[exit]\n\n'
