#!/usr/bin/env python

'''
Created on 25/ott/2009

@author: piero
'''

from listener import *
from clientProxy import *
import sys


class ClientOutput(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.__running = False
    
    
    def print_message(self, msg):
        print "[OUT] %s" % msg

    def set_status(self, msg):
        print "[OUT - Status] %s" % msg

    def stop(self):
        self.__running = False
    
    
    def addClientCallback(self, newClient):
        print "[OUT] Added client %s" % newClient
        
    def clearClientListCallback(self):
        pass
    
    def run(self):
        self.__running = True
        
        print '[o] ClientOutput running'
        
        while self.__running:
            time.sleep(1)
        
        print '[x] ClientOutput'


class ClientInput(threading.Thread):
    
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.__running = False
        
    def stop(self):
        self.__running = False
        
    def run(self):
        self.__running = True
        
        print '[o] ClientInput running'
        
        print 'Line format: DESTINATION MESSAGE'
        
        while self.__running:
            #print '>>>'
            
            try:
                inputready, outputready, exceptready = select.select([sys.stdin], [], [], 1.0)
            except select.error, (value, message):
                print "[!] SELECT ERROR: %s" % str(message)
                continue
            
            for s in inputready:
                line = sys.stdin.readline()
                
                if line == "\n":
                    self.__running = False
                    break
                
                dest, msg = line.split(' ', 2)
                
                print "DEST: %s MSG: %s" % (dest, msg)
                
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
    
    client = ClientProxy(sys.argv[1], int(sys.argv[2]))
    client.logger.setLevel(logging.DEBUG)
    
    # ClientProxy output interface
    client_output = ClientOutput()
    client.interface = client_output
    client.interface.start()
    
    listener = Listener(executor=client, host=sys.argv[1], port=int(sys.argv[2]))

    listener.start()
    client.connect()
    
    # ClientProxy input interface
    client_input = ClientInput(client)
    client_input.start()
    
    while listener.isAlive() and client_input.isAlive():
        time.sleep(1)
    
    # Exit
    client_input.stop()
    client_input.join()
    listener.stop()
    listener.join()
    client_output.stop()
    client_output.join()
    print "Bye :)"
    sys.exit()
