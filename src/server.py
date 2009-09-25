'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *
from masterServer import *
from backupServer import *
from idleServer import *
import time

class Server(ActiveObject):
	
	# Server roles
	MASTER = 'MasterServer'
	BACKUP = 'BackupServer'
	IDLE = 'IdleServer'

	def __init__(self, role = 'undefined'):
		ActiveObject.__init__(self)
		self.__name = str(int(time.time() * 1000))
		self.__strategy = None
		print 'SERVER %s' % self.__name
		
		
	def __del__(self):
		if self.__strategy != None:
			print 'Quitting strategy...'
			self.__strategy.quit()
	
	
	def set_role(self, role, master):
		# Dynamically create the proper class
		try:
			self.__strategy = globals()[role](self)
		except KeyError:
			print "[!] ROLE \"%s\" DOESN'T MAP ANY CLASS!!!\n" % role
			return
		
		if self.__strategy.__class__.__name__ != 'MasterServer' and master != (None, None, None):
			self.__strategy.set_master(master)
		
	
	def get_name(self):
		return self.__name
	

	def _process_request(self, msg, address):
		#print 'Processing request:', msg
		#print 'from', address
		
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
