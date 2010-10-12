#!/usr/bin/python

import zmq
import time
from message import *
import random

def main(args):

    myself = args[1]
    print "Hello, I am", myself

    context = zmq.Context()

    # State Back-End	
    statebe = context.socket(zmq.PUB)

    # State Front-End
    statefe = context.socket(zmq.SUB)
    statefe.setsockopt(zmq.SUBSCRIBE, '')
    
    print 'statefe:', statefe

    bind_address = "ipc://" + myself + "-state.ipc"
    print "Binding to", bind_address
    statebe.bind(bind_address)

    for i in range(len(args) - 2):
        endpoint = "ipc://" + args[i + 2] + "-state.ipc"
        print "Connecting to", endpoint
        statefe.connect(endpoint)
        time.sleep(1.0)

    poller = zmq.Poller()
    poller.register(statefe, zmq.POLLIN)

    while True:
    
        poll_timeout = random.uniform(0.5, 1.5) * 1000
        socks = dict(poller.poll(poll_timeout))
        
        if len(socks) > 0:
            if socks[statefe] == zmq.POLLIN:
                msg = Message()
                msg.recv(statefe)
                print 'Received:', msg
        else:
            msg = Message()
            msg.address = bind_address
            msg.data = myself
            msg.send(statebe)
            
######### VERSION USING select() #########
#
#        (sin, sout, serr) = zmq.select([statefe], [], [], 1)
#        
#        if len(sin) != 0:
#            if sin[0] == statefe:
#                msg = statefe.recv()
#                print 'Received:', msg
#            else:
#                print '!!! WRONG SOCKET !!!'
#        else:
#            msg = myself + '-hello'
#            statebe.send(msg)
#            print 'Sent:', msg
#
##########################################

    poller.unregister(statefe)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print "Usage: peering.py <myself> <peer_1> ... <peer_N>"
        raise SystemExit

    main(sys.argv)

