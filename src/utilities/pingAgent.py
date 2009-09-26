'''
Created on 26/set/2009

@author: piero
'''

import threading
import time
from message import *


class PingAgent(threading.Thread):
	
	def __init__(self, caller, is_master=False, interval = 5.0):
		threading.Thread.__init__(self)
		self.__caller = caller
		self.__interval = interval
		self.__is_master = is_master
		self.__running = False
	
	
	def run(self):
		self.__running = True
		
		while self.__running:
			time.sleep(self.__interval)
			
			if not self.__is_master:
				master = self.__caller.get_role().get_master()
				msg = PingMessage(priority=1)
				msg.serverSrc = self.__caller.get_name()
				msg.serverDst = master[0]
				reply = msg.send(master[1], master[2])

				# Master not replying: trigger rescue procedure
				if reply == None:
					print "Master %s not replying!" % master[0]
			
		print "[x] PingAgent"
	
	
	def kill(self):
		self.__running = False
