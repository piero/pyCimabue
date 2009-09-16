#!/usr/bin/env python

from serverProxy import *
import time
import sys


class Client:

	def __init__(self, server_ip = 'localhost', server_port = 50000):
		self.name = str(int(time.time() * 1000))
		self.server_ip = server_ip
		self.server_port = server_port
		print '[ ] Client: ', self.name
	
	def run(self):
		# Connect to the Server
		server = ServerProxy(host = self.server_ip, port = self.server_port, caller = self.name)
		reply = server.connect()
	
		if reply.type == ErrorMessage:
			print '[!] Error connecting to server (', self.server_ip, ':', self.server_port, ')'
			print reply.data
			return

		# Wait for input
		while 1:
			sys.stdout.write('% ')
	
			# Read from stdin
			line = sys.stdin.readline()
			if line == '\n':
				break
	
			reply = server.sendMessage(line)
			print 'Got reply:', reply


# Execution starts here
if __name__ == "__main__":
	client = Client()
	client.run()
	print '[exit]\n\n'
