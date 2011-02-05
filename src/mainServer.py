#!/usr/bin/env python

'''
Created on 20/set/2009

@author: piero
'''

from listener import *
from server import *
from optparse import OptionParser


### EXECUTION STARTS HERE ###

if __name__=="__main__":
	# Parse command-line args
	listen_ip, listen_port = None, None
	
	# Parse command-line arguments   
	usage = "Usage: %prog [options] [local-ip] local-port"
	optionParser = OptionParser(usage=usage, version="pyCimabue Server v1.0")
	optionParser.add_option("-l", "--log-level", action="store", type="int", dest="log_level", help="Log level [1-5]", default=4)
	
	(options, args) = optionParser.parse_args()
	if len(args) < 1: optionParser.error("Incorrect number of arguments.")
	elif len(args) == 1: listen_port = int(args[0])
	elif len(args) == 2:
		listen_ip = args[0]
		listen_port = int(args[1])
	
	# Create Server, Listener and start
	server = Server()
	
	 # Set log level
	if options.log_level == 1: log_level = logging.CRITICAL
	elif options.log_level == 2: log_level = logging.ERROR
	elif options.log_level == 4: log_level = logging.INFO
	elif options.log_level == 3: log_level = logging.WARNING
	elif options.log_level == 5: log_level = logging.DEBUG
	server.logger.setLevel(log_level)
	
	if listen_ip is not None:
		listener = Listener(executor=server, host=listen_ip, port=listen_port)
	elif listen_port is not None:
		# Use default port
		listener = Listener(executor=server, port=listen_port)
	else:
		# Use default ip:port
		listener = Listener(executor=server)
		
	listener.start()
	
	
	# Set Server server_role
	server.query_role()
	
	
	# Sleep
	while listener.is_alive():
		time.sleep(1)
	
	# Exit
	listener.stop()
	print 'Bye :)'
	sys.exit()
