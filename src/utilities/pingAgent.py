'''
Created on 26/set/2009

@author: piero
'''

import threading
import time
from message import *


class PingAgent(threading.Thread):
	
	def __init__(self, caller, as_master=False, interval = 5.0):
		threading.Thread.__init__(self)
		self.__caller = caller
		self.__interval = interval
		self.is_master = as_master
		self.__running = False
	
	
	def run(self):
		self.__running = True
		
		while self.__running:
			time.sleep(self.__interval)
			
			if self.is_master == True:
				#self.__run_as_master()
				for k in self.__caller.get_role().servers_ping.keys():
					if (time.time() - self.__caller.get_role().servers_ping[k] > 5):
						#del self.__caller.get_role().servers_ping[k]
						
						if k != self.__caller.get_role().backup[0]:
							del self.__caller.get_role().servers[k]
							self.__caller.output("Removed %s (%d servers left)" % (k, len(self.__caller.get_role().servers)),
												logging.WARNING)
							self.__caller.get_role().sync_server_list()
						
						else:
							del self.__caller.get_role().backup
							self.__caller.get_role().backup = None
							self.__caller.output("Backup left (%s)!" % k,
												logging.WARNING)
							# TODO: Start Backup rescue procedure!
						
						del self.__caller.get_role().servers_ping[k]
			else:
				#self.__run_as_slave()
				master = self.__caller.get_role().get_master()
				self.__caller.output("Pinging Master: %s (%s:%d)" % (master[0], master[1][0], master[1][1]))
				msg = PingMessage(priority=1)
				msg.serverSrc = self.__caller.get_name()
				msg.serverDst = master[0]
				reply = msg.send(master[1][0], master[1][1])
		
				# Master not replying: trigger rescue procedure
				if reply == None:
					self.__caller.output(("Master %s not replying!" % master[0]), logging.WARNING)
					
					if self.__caller.get_role().name == self.__caller.BACKUP:
						self.__caller.get_role().elect_new_master()
				
				# Master has changed, make it know we're here
				elif reply.type == "ErrorMessage":
					self.__caller.output(("Master %s doesn't know me" % master[0]), logging.WARNING)
					self.__caller.query_role()
					
		self.__caller.output("[x] PingAgent", logging.INFO)
	
	
	def kill(self):
		self.__running = False


	def __run_as_master(self):
		for k in self.__caller.get_role().servers_ping.keys():
			if (time.time() - self.__caller.get_role().servers_ping[k] > 5):
				del self.__caller.get_role().servers_ping[k]
				
				if k != self.__caller.get_role().backup[0]:
					del self.__caller.get_role().servers[k]
					self.__caller.output("Removed %s (%d servers left)" % (k, len(self.__caller.get_role().servers)),
										logging.WARNING)
					self.__caller.get_role().sync_server_list()
				else:
					del self.__caller.get_role().backup
					self.__caller.get_role().backup = None
					self.__caller.output("Backup left (%s)!" % k,
										logging.WARNING)
					# TODO: Start Backup rescue procedure!
	
	
	def __run_as_slave(self):
		master = self.__caller.get_role().get_master()
		self.__caller.output("Pinging Master: %s (%s:%d)" % (master[0], master[1][0], master[1][1]))
		msg = PingMessage(priority=1)
		msg.serverSrc = self.__caller.get_name()
		msg.serverDst = master[0]
		reply = msg.send(master[1][0], master[1][1])

		# Master not replying: trigger rescue procedure
		if reply == None:
			self.__caller.output(("Master %s not replying!" % master[0]), logging.WARNING)
			
			if self.__caller.get_role().name == self.__caller.BACKUP:
				self.__caller.get_role().elect_new_master()
		
		# Master has changed, make it know we're here
		elif reply.type == "ErrorMessage":
			self.__caller.output(("Master %s doesn't know me" % master[0]), logging.WARNING)
			self.__caller.query_role()
	