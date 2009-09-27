#!/usr/bin/env python

'''
Created on 20/set/2009

@author: piero
'''

from listener import *
from server import *
import time



### EXECUTION STARTS HERE ###

if __name__=="__main__":
	# Parse command-line args
	listen_ip, listen_port = None, None
	
	if len(sys.argv) == 2:
		listen_port = int(sys.argv[1])
	elif len(sys.argv) == 3:
		listen_ip = sys.argv[1]
		listen_port = int(sys.argv[2])
	
	
	# Create Server, Listener and start
	server = Server()
	
	if listen_ip != None:
		listener = Listener(executioner=server, host=listen_ip, port=listen_port)
	elif listen_port != None:
		listener = Listener(executioner=server, port=listen_port)
	else:
		listener = Listener(executioner=server)
		
	listener.start()
	
	
	# Set Server server_role
	#(server_role, master) = server.query_server_role(listener.get_host_and_port())
	#server.set_role(server_role, master)
	server.query_role()
	
	
	# Sleep
	while listener.is_alive():
		time.sleep(1)
	
	# Exit
	print 'Bye :)'

