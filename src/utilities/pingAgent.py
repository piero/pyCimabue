'''
Created on 26/set/2009

@author: piero
'''

import threading
import time
from message import *


class PingAgent(threading.Thread):
    
    def __init__(self, caller, run_as_server=False, interval=5.0):
        threading.Thread.__init__(self)
        self.__caller = caller
        self.__interval = interval
        self.__SERVER_TIMEOUT = 10.0
        self.__CLIENT_TIMEOUT = 5.0
        self.__is_server = run_as_server
        self.__running = False
        if self.__is_server:
            self.__caller.output("[ ] Ping Agent - running as Server")
        else:
            self.__caller.output("[ ] Ping Agent - running as Client")
    
    
    def run(self):
        self.__running = True
        
        while self.__running:
            time.sleep(self.__interval)
            
            if not self.__running:
                break
            
            if self.__is_server:
                if self.__caller.get_role().__class__.__name__ == self.__caller.MASTER:
                    self.__run_as_master()
                else:
                    self.__run_as_slave()
            else:
                self.__run_as_client()
                    
        self.__caller.output("[x] PingAgent", logging.INFO)
    
    
    def stop(self):
        self.__running = False


    def __run_as_master(self):
        # Check other servers
        self.__caller.servers_lock.acquire()
        for k in self.__caller.servers_ping.keys():
            if (time.time() - self.__caller.servers_ping[k] > self.__SERVER_TIMEOUT):
                del self.__caller.servers_ping[k]
                
                if self.__caller.get_role().backup != None and k != self.__caller.get_role().backup[0]:
                    del self.__caller.servers[k]
                    self.__caller.output("[-] Removed %s (%d servers left)" % (k, len(self.__caller.servers)),
                                        logging.WARNING)
                    self.__caller.servers_lock.release()
                    self.__caller.get_role().sync_server_list()
                    self.__caller.servers_lock.acquire()
                
                else:
                    del self.__caller.get_role().backup
                    self.__caller.get_role().backup = None
                    
                    # Elect a new Backup server
                    self.__caller.output("[!] Backup Server left (%s)!" % k, logging.WARNING)
                    self.__caller.servers_lock.release()
                    self.__caller.get_role().elect_backup_server()
                    self.__caller.servers_lock.acquire()
                    
        self.__caller.servers_lock.release()
                
        # Check clients
        self.__caller.clients_lock.acquire()
        
        try:
            for k in self.__caller.clients_ping.keys():
                if (time.time() - self.__caller.clients_ping[k] > self.__CLIENT_TIMEOUT):
                    del self.__caller.clients_ping[k]
                    del self.__caller.clients[k]
                    self.__caller.output("[-] Removed %s (%d clients left)" % (k, len(self.__caller.clients)),
                                            logging.WARNING)
                    
                    self.__caller.clients_lock.release()
                    self.__caller.get_role().sync_client_list()
                    self.__caller.get_role().sync_backup_client_list()
                    self.__caller.clients_lock.acquire()
        
        except KeyError:
            pass
        
        finally:    
            self.__caller.clients_lock.release()

    
    def __run_as_slave(self):
        master = self.__caller.get_role().get_master()
        self.__caller.output("Pinging Master: %s (%s:%d)" % (master[0], master[1][0], master[1][1]))
        msg = PingMessage(priority=1)
        msg.serverSrc = self.__caller.get_name()
        msg.serverDst = master[0]
        reply = msg.send(master[1][0], master[1][1])

        # Master not replying: trigger rescue procedure
        if reply == None:
            self.__caller.output(("[!] Master %s not replying!" % master[0]), logging.WARNING)
            
            if self.__caller.get_role().name == self.__caller.BACKUP:
                attempts = 3
                result = False
                while self.__caller.get_role().name == self.__caller.BACKUP and \
                                                            result == False and \
                                                            attempts > 0:
                    result = self.__caller.get_role().elect_new_master()
                    attempts -= 1
                if result == False:
                    self.__caller.output("[!] Can't elect a new master", logging.ERROR)
        
        # Master has changed, make it know we're here
        elif reply.type == "ErrorMessage":
            self.__caller.output(("[!] Master %s doesn't know me" % master[0]), logging.WARNING)
            self.__caller.query_role()
    
    
    def __run_as_client(self):
        self.__caller.output("Pinging Master: %s (%s:%d)" % (self.__caller.master_name,
                                                                    self.__caller.master_ip,
                                                                    self.__caller.master_port))
        msg = PingMessage(priority=1)
        msg.clientSrc = self.__caller.get_name()
        msg.serverDst = self.__caller.master_name
        reply = msg.send(self.__caller.master_ip, self.__caller.master_port)
        
        if reply != None and reply.type == 'ErrorMessage':
            self.__caller.output(("[!] Master %s doesn't know me" % self.__caller.master_name), logging.WARNING)
            self.__caller.connect_to_server(self.__caller.master_ip, self.__caller.master_port)
        
        # TODO: if reply == None --> Disconnected from Server!
