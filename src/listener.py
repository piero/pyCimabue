'''
Created on 20/set/2009

@author: piero
'''

import select
import socket
import sys
from activeObject import *
from utilities.nullHandler import *
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
		self.__running = False
		self.__executioner = executioner
		self.__executioner.set_listener(self)
		
		# Logging
		logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
		self.__logger = logging.getLogger('Listener')
		self.__logger.setLevel(logging.DEBUG)
		h = NullHandler()
		self.__logger.addHandler(h)
	
	
	def get_host_and_port(self):
		return (self.__HOST, self.__PORT)
	
	
	def stop(self):
		self.__running = False
	
	
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
			self.__logger.error("Couldn\'t open socket: %s (%d)" % (str(message), value))
			sys.exit(1)
			
		input = [listen_skt, sys.stdin]
		self.__running = True

		# The big loop
		while self.__running:
			try:
				inputready, outputready, exceptready = select.select(input,
																	[],
																 	[],
																	self.__SELECT_TIMEOUT)
			except socket.error, (value, message):
				self.__logger.error("[!] SOCKET ERROR: %s" % str(message))
				listen_skt.close()
				
				# Create a new listen socket
				try:
					listen_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					listen_skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					listen_skt.bind((self.__HOST, self.__PORT))
					self.__logger.info("Listening on %s:%d..." % (self.__HOST, self.__PORT))
					listen_skt.listen(self.__backlog)
		
				except socket.error, (value, message):
					if listen_skt:
						listen_skt.close()
					self.__logger.error("Couldn\'t open socket: %s (%d)" % (str(message), value))
					sys.exit(1)
				
				input = [listen_skt, sys.stdin]
				continue
				
			for skt in inputready:
				
				if skt == listen_skt:
					# Handle server socket
					new_skt, address = skt.accept()
					new_skt.settimeout(self.__RECV_TIMEOUT)
					input.append(new_skt)
			
				elif skt == sys.stdin:
					# Handle stdin: exit
					sys.stdin.readline()
					self.__running = False
			
				else:
					# Handle a client socket
					try:
						data = skt.recv(self.__MAX_SIZE)
						
					except socket.timeout, message:
						if skt:
							self.__logger.error("Timeout: socket %d closed" % skt.fileno())
							skt.close()
						continue
						
					except socket.error, (value, message):
						self.__logger.error("Socket Exception: %s" % str(message))
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
					
					else:
						input.remove(skt)
						break

		# Exit
		if skt: skt.close()
		listen_skt.close()
		self.__executioner.stop()
		self.__logger.debug("Joining executioner...")
		self.__executioner.join(2.0)
		self.__logger.info("[x] %s" % self.__class__.__name__)