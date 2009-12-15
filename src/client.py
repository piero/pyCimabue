'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from utilities.xmlParser import *
from utilities.pingAgent import *
import time


class Client(ActiveObject):
	
	def __init__(self, ip, port):
		ActiveObject.__init__(self)
		self.__name = str(int(time.time() * 1000))
		self.skt = None
		self.ip = ip
		self.port = port
		self.server_ip = None
		self.server_port = None
		self.server_name = None
		self.__listener = None
		self.__clients = []
		self.__connected = False
		self.__ping_agent = None
		self.output(("CLIENT %s" % self.__name), logging.INFO)
	
	
	def __del__(self):
		self.output("[x] Client", logging.INFO)
		self.__ping_agent.stop()
	
	
	def get_name(self):
		return self.__name
	
	
	def set_listener(self, listener):
		self.__listener = listener
		
	
	def connect(self):
		parser = XMLParser('server_list.xml')
		output_list = parser.get_output_list()
		self.__connected = False
		
		for i in range(len(output_list)):
			self.output("Connecting to %s:%s..." % (output_list[i][0], output_list[i][1]))	
			if self.connect_to_server(output_list[i][0], int(output_list[i][1])):
				break
		
		if not self.__connected:
			self.output("No server found!", logging.CRITICAL)
			return False
		
		else:
			self.output("Connected to %s (%s:%d)" % (self.server_name, self.server_ip, self.server_port))
			
			# Start the Ping Agent
			self.__ping_agent = PingAgent(caller=self, run_as_server=False)
			self.__ping_agent.start()
			return True
	
	
	def send_message(self, destination, message):
		if destination not in self.__clients:
			self.interface.print_message("Destination %s doesn't exists" % destination)
			return None
		
		# Create the message to send
		msg = SendMessage(self.skt)
		msg.clientSrc = self.__name
		msg.clientDst = destination
		msg.serverDst = self.server_name
		msg.data = message
		
		# Send the message
		reply = msg.send()
		if reply == None:
			if self.interface != None:
				self.interface.print_message("Error sending message to %s: %s" % (destination, msg.data))
		
		return reply
	

	def _process_request(self, msg, address):
		# Dynamically call the proper function
		try:
			process_function_name = "_process_" + msg.type
			process_function = getattr(self, process_function_name)
		
		except AttributeError:
			reply = ErrorMessage(msg.skt, msg.priority)
			reply.serverSrc = self.__name
			reply.clientDst = msg.clientSrc
			reply.data = "Unknown message type: " + msg.type
		
		reply = process_function(msg)
		self._requests.task_done()

		if msg.wait_for_reply():
			reply.reply(reply.skt)
	
		
	def _process_SendMessage(self, msg):
		print 'Processing SendMessage'
		
		if self.interface != None:
			self.interface.print_message("%s: %s" % (msg.clientSrc, msg.data))
		
		reply = Message(msg.skt, msg.priority)
		reply.clientSrc = self.__name
		reply.clientDst = msg.clientSrc
		reply.serverDst = msg.serverSrc
		return reply

	
	def _process_PingMessage(self, msg):
		print 'Processing PingMessage'
		
	
	def _process_errorMessage(self, msg):
		print 'Processing ErrorMessage'
	
	
	def _process_SyncClientListMessage(self, msg):
		self.output(("Received ClientList from %s" % msg.serverSrc), logging.INFO)
		c_names = pickle.loads(msg.data)
		
		self.__update_client_list(c_names)
		
		reply = SyncClientListMessage(msg.skt, msg.priority)
		reply.clientSrc = self.__name
		reply.serverDst = msg.serverSrc
		return reply
	
	
	def connect_to_server(self, server_ip, server_port):
		# Look for the Master Server
		self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.skt.connect((server_ip, server_port))
		except socket.error:
			if self.skt: self.skt.close()
			return False

		# Send 'Hello' message
		msg = ConnectMessage(self.skt, priority=0)
		msg.clientSrc = self.__name			# Our Name
		msg.serverDst = self.ip				# Our IP address
		msg.data = str(self.port)			# Our Port
		reply = msg.send()
		
		if reply != None:
			self.__connected = True
			if self.skt: self.skt.close()

			if reply.type != "SyncClientListMessage":
				self.output("Oops, wrong server!", logging.WARNING)
				return False	# Oops, it wasn't the Master Server
			
			else:
				self.server_ip = server_ip
				self.server_port = server_port
				self.server_name = reply.serverSrc
				
				# Update clients list
				if reply.data != None:
					c_names = pickle.loads(reply.data)
					self.__update_client_list(c_names)
		
		return True
	
	
	def __update_client_list(self, client_list):
		# Clear the clients list
		while len(self.__clients):
			self.__clients.pop()
		
		for i in client_list:
			if i != self.__name:
				self.__clients.append(i)
		
		# Print Client list (debug)
		self.output("CLIENT LIST (%d clients except me)" % len(self.__clients))
		for c in self.__clients:
			self.output("%s" % c)