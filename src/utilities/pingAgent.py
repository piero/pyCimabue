'''
Created on 26/set/2009

@author: piero
'''

import threading
import time
from message import *


class PingAgent(threading.Thread):
	
	def __init__(self, caller, run_as_server=False, interval=5.0):
		threading.Thread.__init__(self)
		self.__caller = caller
		self.__interval = interval
		self.__SERVER_TIMEOUT = 5.0
		self.__CLIENT_TIMEOUT = 5.0
		self.__is_server = run_as_server
		self.__running = False
		if self.__is_server:
			self.__caller.output("[ ] Ping Agent - running as Server")
		else:
			self.__caller.output("[ ] Ping Agent - running as Client")
	
	
	def run(self):
		self.__running = True
		
		while self.__running:
			time.sleep(self.__interval)
			
			if self.__is_server:
				
				if self.__caller.get_role().__class__.__name__ == self.__caller.MASTER:
					self.__run_as_master()
				
				else:
					self.__run_as_slave()
			
			else:
				self.__run_as_client()
					
		self.__caller.output("[x] PingAgent", logging.INFO)
	
	
	def stop(self):
		self.__running = False


	def __run_as_master(self):
		# Check other servers
		for k in self.__caller.get_role().servers_ping.keys():
			if (time.time() - self.__caller.get_role().servers_ping[k] > self.__SERVER_TIMEOUT):
				del self.__caller.get_role().servers_ping[k]
				
				if self.__caller.get_role().backup != None and k != self.__caller.get_role().backup[0]:
					del self.__caller.get_role().servers[k]
					self.__caller.output("Removed %s (%d servers left)" % (k, len(self.__caller.get_role().servers)),
										logging.WARNING)
					self.__caller.get_role().sync_server_list()
				
				else:
					del self.__caller.get_role().backup
					self.__caller.get_role().backup = None
					self.__caller.output("Backup Server left (%s)!" % k, logging.WARNING)
					# TODO: Start Backup rescue procedure!
				
		# Check clients
		self.__caller.get_role().clients_lock.acquire()
		for k in self.__caller.get_role().clients_ping.keys():
			if (time.time() - self.__caller.get_role().clients_ping[k] > self.__CLIENT_TIMEOUT):
				del self.__caller.get_role().clients_ping[k]
				del self.__caller.get_role().clients[k]
				self.__caller.output("Removed %s (%d clients left)" % (k, len(self.__caller.get_role().clients)),
										logging.WARNING)
				
				self.__caller.get_role().clients_lock.release()
				self.__caller.get_role().sync_client_list()
				self.__caller.get_role().clients_lock.acquire()
				
		self.__caller.get_role().clients_lock.release()

	
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
	
	
	def __run_as_client(self):
		self.__caller.output("Pinging Master: %s (%s:%d)" % (self.__caller.server_name,
																	self.__caller.server_ip,
																	self.__caller.server_port))
		msg = PingMessage(priority=1)
		msg.clientSrc = self.__caller.get_name()
		msg.serverDst = self.__caller.server_name
		reply = msg.send(self.__caller.server_ip, self.__caller.server_port)
		
		if reply == None or reply.type == 'ErrorMessage':
			self.__caller.output(("Master %s doesn't know me" % self.__caller.server_name), logging.WARNING)
			self.__caller.connect_to_server(self.__caller.server_ip, self.__caller.server_port)