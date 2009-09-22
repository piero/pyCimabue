'''
Created on 20/set/2009

@author: piero
'''

import threading
from message import *
from Queue import PriorityQueue, Empty, Full


class ActiveObject(threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		self._requests = PriorityQueue()
		self._running = True
		self.ip = None
		self.port = None


	def add_request(self, msg, address):
		if (msg.priority >= 0) and (msg.priority <= 3):
			self._requests.put((msg.priority, (msg, address)))
		else:
			print '[!] Request ignored: wrong priority (%d)' % msg.priority


	def _get_next_request(self):
		try:
			# Wait until a request is available
			request = self._requests.get(block = True, timeout = 1.0)
			return request
		except Empty:
			pass
		return None
	
	
	def _process_request(self, msg, address):
		pass
	

	def run(self):
		while self._running == True:
			req = self._get_next_request()
			if req:
				self._process_request(req[1][0], req[1][1])
		print '[x] %s' % self.__class__.__name__


	def kill(self):
		self._running = False
	