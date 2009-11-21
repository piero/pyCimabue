#!/usr/bin/env python

'''
Created on 25/ott/2009

@author: piero
'''

from listener import *
from client import *
import sys



### EXECUTION STARTS HERE ###

if __name__=="__main__":
	
	# Check command-line arguments
	if len(sys.argv) < 3:
		print 'Usage:', sys.argv[0], 'ip port'
		sys.exit(1)
	
	
	client = Client(sys.argv[1], int(sys.argv[2]))
	client.logger.setLevel(logging.DEBUG)
	
	listener = Listener(executioner=client, host=sys.argv[1], port=int(sys.argv[2]))
	
	client.connect()
	
	
	listener.start()
	

	# Take user imput
	while listener.is_alive():
		print 'Destination > '
		dest = sys.stdin.readline()
		if dest == '\n': break
		
		print 'Message > '
		msg = sys.stdin.readline()
		if msg == '\n': break
		
		reply = client.send_message(dest.rstrip('\n'), msg.rstrip('\n'))
		print 'Reply', reply, '\n'
		
		time.sleep(1)
	
	# Exit
	listener.stop()
	print "Bye :)"
