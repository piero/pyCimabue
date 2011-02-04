#!/usr/bin/env python

'''
Created on 25/ott/2009

@author: piero
'''

from listener import *
from clientProxy import *
import sys
from optparse import OptionParser

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
    
    def __init__(self, proxy):
        threading.Thread.__init__(self)
        self.__running = False
        self.proxy = proxy
        
    def stop(self):
        self.__running = False
    
    def __printClientList(self, clients):
        print "   Connected clients"
        print "-----------------------"
        if len(clients) > 0:
            for c in clients:
                print c
        else:
            print " No clients connected"
        print "-----------------------\n"
    
    def run(self):
        self.__running = True
        
        print '[o] ClientInput running'
        print "Line format: DESTINATION MESSAGE ('x' to terminate)"
        
        while self.__running:
            try:
                inputready, outputready, exceptready = select.select([sys.stdin], [], [], 1.0)
            except select.error, (value, message):
                print "[!] SELECT ERROR: %s" % str(message)
                continue
            
            for s in inputready:
                line = sys.stdin.readline()
                if line == "" or line == "\n":
                    continue
                # Quit
                if line == "x\n":
                    self.__running = False
                    break
                # Client list
                elif line == "l\n":
                    self.__printClientList(self.proxy.getClientList())
                # Send a message
                else:
                    dest, msg = line.split(' ', 2)
                
                    print "DEST: %s MSG: %s" % (dest, msg)
                
                    reply = self.proxy.send_message(dest.rstrip('\n'), msg.rstrip('\n'))
                    if reply is not None:
                        print "> %s: %s\n" % (dest, msg)
        
        print '[x] ClientInput'
    

### EXECUTION STARTS HERE ###

if __name__=="__main__":
    
    # Parse command-line arguments   
    usage = "Usage: %prog [options] local-ip local-port"
    optionParser = OptionParser(usage=usage, version="pyCimabue Client v1.0")
    optionParser.add_option("-l", "--log-level", action="store", type="int", dest="log_level", help="Log level [1-5]", default=4)
    
    (options, args) = optionParser.parse_args()
    if len(args) != 2:
        optionParser.error("Incorrect number of arguments.")
    
    # Create the ClientProxy
    proxy = ClientProxy(args[0], int(args[1]))
    
    # ClientProxy output interface
    client_output = ClientOutput()
    proxy.interface = client_output
    proxy.interface.start()
    
    listener = Listener(executor=proxy,
                        host=args[0],
                        port=int(args[1]),
                        use_stdin=False)
    
    # Set log level
    if options.log_level == 1: log_level = logging.CRITICAL
    elif options.log_level == 2: log_level = logging.ERROR
    elif options.log_level == 4: log_level = logging.INFO
    elif options.log_level == 3: log_level = logging.WARNING
    elif options.log_level == 5: log_level = logging.DEBUG
    listener.setLogLevel(log_level)
    
    # Start the Client and connect
    listener.start()
    proxy.connect()
    
    # Start the Interface and the Listener
    client_input = ClientInput(proxy)
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
