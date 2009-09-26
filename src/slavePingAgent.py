'''
Created on 26/set/2009

@author: piero
'''

import threading
import time
from message import *


class SlavePingAgent(threading.Thread):
	
	def __init__(self, caller, interval=5.0):
		threading.Thread.__init__(self)
		self.__caller = caller
		self.__interval = interval
		self.__running = False
		
	
	def run(self):
		self.__running = True
		
		while self.__running:
			time.sleep(self.__interval)
			master = self.__caller.get_master()
			msg = PingMessage(priority=1)
			msg.serverSrc = self.__caller.get_server_name()
			msg.serverDst = master[0]
			reply = msg.send(master[1], master[2])

			# Master not replying: trigger rescue procedure
			if reply == None:
				print "Master %s not replying!" % master[0]
			
		print "[x] Slave Ping Agent"

		
	def quit(self):
		self.__running = False