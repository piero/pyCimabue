import threading
import time
from Queue import *


class SyncManager(threading.Thread):

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

			if cmd == 'S':
				self.__server.sync_server_list()
				print 'SYNC SERVER LIST'
			elif cmd == 'C':
				print 'SYNC CLIENT LIST (unsupported)'
				pass
		
		print '[x] SyncManager'
		
	
	def quit(self):
		self.__running = False
