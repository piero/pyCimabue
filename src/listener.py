'''
Created on 20/set/2009

@author: piero
'''

import select
import socket
import sys
from activeObject import *
import threading


class Listener(threading.Thread):
	
	def __init__(self, executioner, host = '127.0.0.1', port = 50000):
		threading.Thread.__init__(self)
		self.__HOST = host
		self.__PORT = port
		self.__backlog = 5
		self.__MAX_SIZE = 1024
		self.__SELECT_TIMEOUT = 1.0
		self.__RECV_TIMEOUT = 5.0
		self.__executioner = executioner
		self.__executioner.set_listener(self)
		
		# Logging
		self.__logger = logging.getLogger('Listener')
		self.__logger.setLevel(logging.DEBUG)
		console = logging.StreamHandler()
		console.setLevel(logging.DEBUG)
		formatter = logging.Formatter('[%(levelname)s] %(message)s')
		console.setFormatter(formatter)
		self.__logger.addHandler(console)
	
	
	def get_host_and_port(self):
		return (self.__HOST, self.__PORT)
	
	
	def run(self):
		# Start active object
		self.__executioner.ip = self.__HOST
		self.__executioner.port = self.__PORT
		self.__executioner.start()
		
		try:
			listen_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			listen_skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			listen_skt.bind((self.__HOST, self.__PORT))
			self.__logger.info("Listening on %s:%d..." % (self.__HOST, self.__PORT))
			listen_skt.listen(self.__backlog)

		except socket.error, (value, message):
			if listen_skt:
				listen_skt.close()
			print 'Couldn\'t open socket: %s (%d)' % (str(message), value)
			sys.exit(1)
			
		input = [listen_skt, sys.stdin]
		running = True

		# The big loop
		while running:
			try:
				inputready, outputready, exceptready = select.select(input,
																	[],
																 	[],
																	self.__SELECT_TIMEOUT)
			except socket.error, (value, message):
				print '[!] SOCKET ERROR:', str(message)
				running = False
				
			for skt in inputready:
	
				if skt == listen_skt:
					# Handle server socket
					new_skt, address = skt.accept()
					#print 'New connection from', address
					new_skt.settimeout(self.__RECV_TIMEOUT)
					input.append(new_skt)
			
				elif skt == sys.stdin:
					# Handle stdin: exit
					sys.stdin.readline()
					running = False
			
				else:
					# Handle a client socket
					try:
						data = skt.recv(self.__MAX_SIZE)
						
					except socket.timeout, message:
						if skt:
							print 'Timeout: socket %d closed' % skt.fileno()
							skt.close()
						continue
						
					except socket.error, (value, message):
						print 'Socket Exception:', str(message)
						if skt:
							skt.close()
						continue
					
					if data:
						try:
							msg = Message(skt)
							msg_dict = pickle.loads(data)
							msg.dict2msg(msg_dict)
							self.__executioner.add_request(msg, address)
							
						except KeyError:
							pass
						except IndexError:
							pass

		# Exit
		listen_skt.close()
		self.__executioner.kill()
		print 'Joining executioner...'
		self.__executioner.join(10.0)
		print '[x] %s' % self.__class__.__name__