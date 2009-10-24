'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from serverStrategies.masterStrategy import *
from serverStrategies.backupStrategy import *
from serverStrategies.idleStrategy import *
from utilities.pingAgent import *
from utilities.xmlParser import *
import time

class Server(ActiveObject):
	
	# Server roles
	MASTER = 'MasterStrategy'
	BACKUP = 'BackupStrategy'
	IDLE = 'IdleStrategy'

	def __init__(self, role = 'undefined'):
		ActiveObject.__init__(self)
		self.__name = str(int(time.time() * 1000))
		self.__listener = None
		self.__strategy = None
		self.__ping_agent = None
		print 'SERVER %s' % self.__name
	
	
	def kill(self):
		self._running = False
		self._kill_dependancies()
			
	
	def _kill_dependancies(self):
		if self.__strategy != None:
			print '[x] Exiting strategy...'
			self.__strategy.exit()
			
		if self.__ping_agent != None:
			print '[x] Killing Ping Agent...'
			self.__ping_agent.kill()
			if self.__ping_agent.is_alive():
				self.__ping_agent.join(2.0)
			#del self.__ping_agent
			self.__ping_agent = None
	
	
	def set_listener(self, listener):
		self.__listener = listener
	
	
	def set_role(self, role, arg=None):
		self._kill_dependancies()
		print 'Setting role:', role
		
		# Dynamically create the proper class
		try:
			self.__strategy = globals()[role](self, arg)
		except KeyError:
			print "[!] ROLE \"%s\" DOESN'T MAP ANY CLASS!!!\n" % role
			return
		
		if (self.__strategy.__class__.__name__ != Server.MASTER):
		#if (self.__strategy.__class__.__name__ != Server.MASTER) and (arg != None):
			#self.__strategy.set_master(arg)
			self.__ping_agent = PingAgent(self, is_master=False)
		else:
			self.__ping_agent = PingAgent(self, is_master=True)
			
		self.__ping_agent.start()
		
	
	def get_role(self):
		return self.__strategy
		
	
	def get_name(self):
		return self.__name
	

	def _process_request(self, msg, address):
		# Dynamically call the proper function
		try:
			function_name = "_process_" + msg.type
			reply = getattr(self.__strategy, function_name)(msg)
		except AttributeError:
			reply = ErrorMessage(msg.skt, msg.priority)
			reply.serverSrc = self.__name
			reply.clientDst = msg.clientSrc
			reply.data = "Unknown message type: " + msg.type
		
		self._requests.task_done()

		if msg.wait_for_reply():
			reply.reply(reply.skt)


	def _check_recipient(self, msg):
		if msg.serverDst == self.__name:
			return True
		else:
			print "[!] Request for %s, but I am %s" % (msg.serverDst, self.__name)
			return False
		
	
	def query_role(self):
		parser = XMLParser('server_list.xml')
		output_list = parser.get_output_list()
		connected = False
		
		for i in range(len(output_list)):		
			# Skip ourselves
			host_and_port = self.__listener.get_host_and_port()
			if output_list[i][0] == host_and_port[0] and int(output_list[i][1]) == host_and_port[1]:
				continue
			
			print "[%d] Trying %s:%s..." % (i, output_list[i][0], output_list[i][1])
			
			# Look for the Master Server
			skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				skt.connect((output_list[i][0], int(output_list[i][1])))
			except socket.error:
				if skt:	skt.close()
				continue
	
			# Send 'Hello' message
			msg = HelloMessage(skt, priority=0)
			msg.serverSrc = self.__name				# Our Name
			msg.clientSrc = self.ip					# Our IP address
			msg.clientDst = str(self.port)			# Our Port
			reply = msg.send()
			if reply != None:
				connected = True				
			if skt: skt.close()

			if reply.type == 'ErrorMessage':
				continue	# Oops, it wasn't the Master Server
			
			elif reply.type == 'WelcomeBackup':
				self.set_role(Server.BACKUP, (reply.data, (reply.clientSrc, int(reply.clientDst))))
			
			elif reply.type == 'WelcomeIdle':
				self.set_role(Server.IDLE, (reply.data, (reply.clientSrc, int(reply.clientDst))))
			
			else:
				print 'UNKNOWN ROLE:', reply.type
				self.set_role(reply.type)
			# We're done
			return
		
		# We're the Master Server
		if connected == False:
			self.set_role(Server.MASTER)
	
	
		