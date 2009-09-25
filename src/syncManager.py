import threading
import time

class SyncManager(threading.Thread):

    def __init__(self, server, timeout=5):
        threading.Thread.__init__(self)
        self.__server = server
        self.__SYNC_TIMEOUT = timeout
        self.__timer = self.__SYNC_TIMEOUT
        self.__running = False
        print "[o] SyncManager (%d sec)" % self.__SYNC_TIMEOUT
        
    
    def run(self):
        self.running = True
        
        while self.running:
            self.__timer -= 1
            time.sleep(1)
            
            if self.__timer == 0:
                self.__server.sync_server_list()
        
        print '[x] SyncManager'
        
    
    def quit(self):
    	self.__running = False
