#!/usr/bin/env python

from message import *
import sys

# Check command-line arguments
if len(sys.argv) < 3:
    print 'Usage:', sys.argv[0], 'server_ip server_port'
    sys.exit(1)
    

msg_types = [Message,
            ConnectMessage,
            SendMessage,
            AddClientMessage,
            PingMessage, 
            ErrorMessage]

while 1:
    for i in range(len(msg_types)):
        print '[', i, ']', msg_types[i].__name__
   
    sys.stdout.write('Choice? ')
     
    # Read from stdin
    choice = sys.stdin.readline()
    if choice == '\n':
        break

    elif int(choice) not in range(len(msg_types)):
        print '[!] Invalid choice\n'
        continue

    else:
        msg = msg_types[int(choice)]()
        print msg.type
        reply = msg.send(sys.argv[1], int(sys.argv[2]))
        print 'Reply:', reply, '\n'
     
print '[ exit ]'
