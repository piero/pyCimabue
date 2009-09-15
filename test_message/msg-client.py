#!/usr/bin/env python

from message import *
import sys


class ServerProxy:

	def __init__(self, init_host, init_port, caller):
		self.host = init_host
		self.port = init_port
		self.client = caller
		self.server = ''
	
	def connect(self):
		msg = ConnectMessage()
		msg.clientSrc = self.client
		msg.send(self.host, self.port)
		return msg
		
	def sendMessage(self, message):
		msg = SendMessage()
		msg.clientSrc = self.client
		msg.serverDst = self.server
		msg.data = message
		msg.send(self.host, self.port)
		return msg


# Execution starts here
server = ServerProxy('localhost', 50000, '12345')

while 1:
	sys.stdout.write('% ')
	
	# Read from stdin
	line = sys.stdin.readline()
	if line == '\n':
		break
	
	reply = server.connect()
	print 'Got reply:', reply
	
	reply = server.sendMessage(line)
	print 'Got reply:', reply

# Exit
sys.stdout.write('[exit]\n\n')

