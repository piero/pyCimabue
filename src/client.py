'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from utilities.xmlParser import *
import time


class Client(ActiveObject):
	
	def __init__(self, ip, port):
		ActiveObject.__init__(self)
		self.__name = str(int(time.time() * 1000))
		self.ip = ip
		self.port = port
		self.server_ip = None
		self.server_port = None
		self.server_name = None
		self.__listener = None
		self.output(("CLIENT %s" % self.__name), logging.INFO)
	
	
	def set_listener(self, listener):
		self.__listener = listener
		
	
	def connect(self):
		parser = XMLParser('server_list.xml')
		output_list = parser.get_output_list()
		connected = False
		
		for i in range(len(output_list)):
			self.output("[%d] Connecting to %s:%s..." % (i, output_list[i][0], output_list[i][1]))
			
			# Look for the Master Server
			skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				skt.connect((output_list[i][0], int(output_list[i][1])))
			except socket.error:
				if skt:	skt.close()
				continue
	
			# Send 'Hello' message
			msg = ConnectMessage(skt, priority=0)
			msg.clientSrc = self.__name			# Our Name
			msg.serverDst = self.ip				# Our IP address
			msg.data = str(self.port)			# Our Port
			reply = msg.send()
			if reply != None:
				connected = True				
			if skt: skt.close()

			if reply.type == 'ErrorMessage':
				self.output("Oops, wrong server!", logging.WARNING)
				continue	# Oops, it wasn't the Master Server
			
			else:
				self.server_ip = output_list[i][0]
				self.server_port = int(output_list[i][1])
				self.server_name = reply.serverSrc
				self.output("Connected to %s (%s:%d)" % (self.server_name, self.server_ip, self.server_port))
			
			# We're done
			return
		
		# We're the Master Server
		if connected == False:
			self.output("No server found!", logging.CRITICAL)
		else:
			self.output("Connected to %s:%d..." % self.server_ip, self.server_port)
	
	
	def __process_request(self, msg):
		if msg.type == SendMessage:
			self.__process_sendMessage(msg)
		elif msg.type == PingMessage:
			self.__process_pingMessage(msg)
		elif msg.type == ErrorMessage:
			self.__process_errorMessage(msg)
	
		
	def __process_sendMessage(self, msg):
		print 'Processing SendMessage'

	
	def __process_pingMessage(self, msg):
		print 'Processing PingMessage'
		
	
	def __process_errorMessage(self, msg):
		print 'Processing ErrorMessage'
	