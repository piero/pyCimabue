'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from serverStrategies.masterStrategy import *
from serverStrategies.backupStrategy import *
from serverStrategies.idleStrategy import *
from utilities.pingAgent import *
import time

class Server(ActiveObject):
	
	# Server roles
	MASTER = 'MasterStrategy'
	BACKUP = 'BackupStrategy'
	IDLE = 'IdleStrategy'

	def __init__(self, role = 'undefined'):
		ActiveObject.__init__(self)
		self.__name = str(int(time.time() * 1000))
		self.__strategy = None
		self.__ping_agent = None
		print 'SERVER %s' % self.__name
	
	
	def kill(self):
		self._running = False
		if self.__strategy != None:
			print 'Exiting strategy...'
			self.__strategy.exit()
			
		if self.__ping_agent != None and self.__ping_agent.is_alive():
			print 'Killing Ping Agent...'
			self.__ping_agent.kill()
			self.__ping_agent.join(2.0)
			
	
	def set_role(self, role, master=(None, None, None)):
		print 'Setting role:', role
		
		# Dynamically create the proper class
		try:
			self.__strategy = globals()[role](self)
		except KeyError:
			print "[!] ROLE \"%s\" DOESN'T MAP ANY CLASS!!!\n" % role
			return
		
		if self.__strategy.__class__.__name__ != 'MasterStrategy' and master != (None, None, None):
			self.__strategy.set_master(master)
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
