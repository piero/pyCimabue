import threading
import time
from Queue import *


class SyncManager(threading.Thread):

	# Commands
	SYNC_SERVER_LIST = 1
	SYNC_CLIENT_LIST = 2
	

	def __init__(self, server):
		threading.Thread.__init__(self)
		self.__server = server
		self.__running = False
		print "[o] SyncManager"
		
	
	def run(self):
		self.__running = True
		
		while self.__running:
			cmd = ''
			try:
				cmd = self.__server.sync_queue.get(block=True, timeout=1.0)
			except Empty:
				continue

			# Synchronize Server List
			if cmd == self.SYNC_SERVER_LIST:
				self.__server.sync_server_list()
				print '[SYNC SERVER LIST]'
			
			# Synchronize Client List
			elif cmd == self.SYNC_CLIENT_LIST:
				print '[SYNC CLIENT LIST] (unsupported)'
				pass
		
		print '[x] SyncManager'
		
	
	def kill(self):
		self.__running = False
