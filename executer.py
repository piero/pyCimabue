from message import *
import threading
import sys
import select
import Queue

class Executer(threading.Thread):
	
	def __init__(self, client, caller):
		threading.Thread.__init__(self)
		self.client = client
		self.caller = caller
		self.running = False
		
	def run(self):
	
		self.running = True

		while self.running:
			msg = self.caller.msg_queue.get()

			if msg == None:
				self.running = False
				break

			elif msg.type == 'ConnectMessage':
				print 'CONNECT MESSAGE'
			elif msg.type == 'SendMessage':
				print 'SEND MESSAGE'
			elif msg.type == 'AddClientMessage':
				print 'ADD CLIENT MESSAGE'
			elif msg.type == 'PingMessage':
				print 'PING MESSAGE'
			else:
				print 'UNKNOWN MESSAGE'
