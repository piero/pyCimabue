'''
Created on 20/set/2009

@author: piero
'''

from activeObject import *


class Client(ActiveObject):
	
	def __process_request(self, msg):
		if msg.type == SendMessage:
			self.__process_sendMessage(msg)
		elif msg.type == PingMessage:
			self.__process_pingMessage(msg)
		elif msg.type == ErrorMessage:
			self.__process_errorMessage(msg)
	
		
	def __process_sendMessage(self, msg):
		print 'Processing SendMessage'

	
	def __process_pingMessage(self, msg):
		print 'Processing PingMessage'
		
	
	def __process_errorMessage(self, msg):
		print 'Processing ErrorMessage'