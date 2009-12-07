#!/usr/bin/env python

'''
Created on 25/ott/2009

@author: piero
'''

from listener import *
from client import *
import sys


class ClientOutput(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.__running = False
	
	
	def print_message(self, msg):
		print msg


	def stop(self):
		self.__running = False
	
	
	def run(self):
		self.__running = True
		
		while self.__running:
			pass
		
		print '[x] ClientOutput'


class ClientInput(threading.Thread):
	
	def __init__(self, client):
		threading.Thread.__init__(self)
		self.__running = False
		
	def stop(self):
		self.__running = False
		
	def run(self):
		self.__running = True
		
		while self.__running:
			#print '>>>'
			
			try:
				inputready, outputready, exceptready = select.select([sys.stdin], [], [], 1.0)
			except select.error, (value, message):
				print "[!] SELECT ERROR: %s" % str(message)
				continue
			
			for s in inputready:
				line = sys.stdin.readline()
				
				if line == '\n':
					self.__running = False
					break
				
				dest, msg = line.split(' ', 2)
				
				reply = client.send_message(dest.rstrip('\n'), msg.rstrip('\n'))
				if reply != None:
					print 'Reply', str(reply), '\n'
		
		print '[x] ClientInput'
	

### EXECUTION STARTS HERE ###

if __name__=="__main__":
	
	# Check command-line arguments
	if len(sys.argv) < 3:
		print 'Usage:', sys.argv[0], 'ip port'
		sys.exit(1)
	
	client = Client(sys.argv[1], int(sys.argv[2]))
	client.logger.setLevel(logging.DEBUG)
	
	# Client output interface
	client_output = ClientOutput()
	client.interface = client_output
	client.interface.start()
	
	listener = Listener(executioner=client, host=sys.argv[1], port=int(sys.argv[2]))

	listener.start()
	client.connect()
	
	# Client input interface
	client_input = ClientInput(client)
	client_input.start()
	
	while listener.isAlive() and client_input.isAlive():
		time.sleep(1)
	
	# Exit
	client_input.stop()
	listener.stop()
	client_output.stop()
	print "Bye :)"
	sys.exit()
