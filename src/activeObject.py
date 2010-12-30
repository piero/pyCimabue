'''
Created on 20/set/2009

@author: piero
'''

import threading
from message import *
from utilities.nullHandler import *
from Queue import PriorityQueue, Empty, Full


class ActiveObject(threading.Thread):

    # Request types
    LOCAL_REQUEST = 0
    REMOTE_REQUEST = 1 

    def __init__(self):
        threading.Thread.__init__(self)
        self._requests = PriorityQueue()
        self._running = True
        self.ip = None
        self.port = None
        self.interface = None
        
        # Logging
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
        self.logger = logging.getLogger('ActiveObject')
        self.logger.setLevel(logging.DEBUG)
        h = NullHandler()
        self.logger.addHandler(h)


    def add_request(self, msg, type):
        if msg.priority >= 0:
            self._requests.put((msg.priority, (msg, type)))
        else:
            self.output(("[!] Request ignored: wrong priority (%d)" % msg.priority), logging.WARNING)


    def _get_next_request(self):
        try:
            # Wait until a request is available
            request = self._requests.get(block=True, timeout=1.0)
            return request
        except Empty:
            pass
        return None
    
    
    def _process_request(self, msg, address):
        pass
    

    def run(self):
        while self._running:
            req = self._get_next_request()
            if req:
                self._process_request(req[1][0], req[1][1])
        self.output("[x] %s" % self.__class__.__name__)


    def stop(self):
        self._running = False
    
    
    def output(self, msg, level=logging.DEBUG):
        self.logger.log(level, msg)