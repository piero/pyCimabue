#!/usr/bin/env python

'''
Created on 20/set/2009

@author: piero
'''

from listener import *
from server import *
import time
from xmlParser import *


# Set Server role
def query_server_role(server_name, host_and_port):
	parser = XMLParser('server_list.xml')
	output_list = parser.get_output_list()
	connected = False
	
	for i in range(len(output_list)):		
		# Skip ourselves
		if output_list[i][0] == host_and_port[0] and int(output_list[i][1]) == host_and_port[1]:
			continue
		
		print "[%d] Trying %s:%s..." % (i, output_list[i][0], output_list[i][1])
		
		# Look for the Master Server
		skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			skt.connect((output_list[i][0], int(output_list[i][1])))
		except socket.error:
			if skt:	skt.close()
			continue

		# Send 'Hello' message
		msg = HelloMessage(skt, priority=0)
		msg.serverSrc = server_name				# Our Name
		msg.clientSrc = host_and_port[0]		# Our IP address
		msg.clientDst = str(host_and_port[1])	# Our Port
		reply = msg.send()
		print "1) Sent message to %s:%d" % (output_list[i][0], int(output_list[i][1]))
		connected = True
			
		if skt: skt.close()
	
		print 'REPLY:', str(reply)
		
		if reply.type == 'ErrorMessage':
			continue	# We didn't contact the Master Server			
		elif reply.type == 'WelcomeBackup':
			return (Server.BACKUP, (reply.data, reply.clientSrc, int(reply.clientDst)))
		elif reply.type == 'WelcomeIdle':
			return (Server.IDLE, (reply.data, reply.clientSrc, int(reply.clientDst)))
		else:
			print 'UNKNOWN ROLE:', reply.type
			return (reply.type, (None, None, None))
	
	# Return role
	if connected == False:
		return (Server.MASTER, (None, None, None))



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
(server_role, master) = query_server_role(server.get_name(), listener.get_host_and_port())
server.set_role(server_role, master)


# Sleep
while listener.isAlive():
	time.sleep(1)

# Exit
print 'Bye :)'

