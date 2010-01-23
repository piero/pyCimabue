#!/usr/bin/env python

from message import *
import sys
import random

# Check command-line arguments
if len(sys.argv) < 3:
    print 'Usage:', sys.argv[0], 'server_ip server_port'
    sys.exit(1)
    
# Connect to Server
try:
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.connect((sys.argv[1], int(sys.argv[2])))
except socket.error, (value, message):
    if skt:
        skt.close()
    logging.error("[!] Message.send(): Socket error: " + str(message))
    sys.exit(1)

msg_types = [Message,
            ConnectMessage,
            SendMessage,
            AddClientMessage,
            PingMessage,
            HelloMessage,
            ErrorMessage]

while 1:
    for i in range(len(msg_types)):
        print '[%d] %s' % (i, msg_types[i].__name__)
   
    print '[%d] Message burst' % len(msg_types)
    sys.stdout.write('Choice? ')
    
    # Read from stdin
    choice = sys.stdin.readline()
    if choice == '\n':
        break

    elif int(choice) not in range(len(msg_types) + 1):
        print '[!] Invalid choice\n'
        continue

    elif int(choice) == len(msg_types):
        # Message burst
        for i in range(10):
            msg = msg_types[random.randint(0, len(msg_types) - 1)](skt, random.randint(0,2), False)
            print '[%d] %s\t(p: %d)' % (i, msg.type, msg.priority)
            msg.clientSrc = str(i)
            msg.data = sys.argv[1]
            msg.send(sys.argv[1], int(sys.argv[2]))

    else:
        msg = msg_types[int(choice)](skt, random.randint(0,2))
        print msg.type
        msg.clientSrc = '12345'
        msg.clientDst = '00000'
        msg.serverDst = '1234567890'
        msg.data = sys.argv[1]
        reply = msg.send(sys.argv[1], int(sys.argv[2]))
        print 'Reply:', reply, '\n'
     
print '[ exit ]'
