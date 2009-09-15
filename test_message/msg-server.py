#!/usr/bin/env python

from message import *
import select
import socket
import sys

host = ''
port = 50000
backlog = 5
size = 1024

try:
	server_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_skt.bind((host, port))
	server_skt.listen(backlog)

except socket.error, (value, message):
	if server_skt:
		server_skt.close()
	print 'Couldn\'t open socket:', message
	sys.exit(1)

input = [server_skt, sys.stdin]
running = 1

while running:
	inputready, outputready, exceptready = select.select(input, [], [])

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
			data = s.recv(size)
			
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
				msg.reply(s)
			else:
				s.close()
				input.remove(s)

# Exit
sys.stdout.write('[exit]\n\n')	
server_skt.close()

