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
		self.is_master = is_master
		self.__running = False
		if self.is_master:
			print '[o] PingAgent (Master)'
		else:
			print '[o] PingAgent (Slave)'
		
	
	def run(self):
		self.__running = True
		
		while self.__running:
			time.sleep(self.__interval)
			
			if self.is_master == False:
				master = self.__caller.get_role().get_master()
				print "Pinging Master: %s (%s:%d)" % (master[0], master[1][0], master[1][1])
				msg = PingMessage(priority=1)
				msg.serverSrc = self.__caller.get_name()
				msg.serverDst = master[0]
				reply = msg.send(master[1][0], master[1][1])

				# Master not replying: trigger rescue procedure
				if reply == None:
					print "Master %s not replying!" % master[0]
					
					if self.__caller.get_role().name == self.__caller.BACKUP:
						self.__caller.get_role().elect_new_master()
			
		print "[x] PingAgent"
	
	
	def kill(self):
		self.__running = False
