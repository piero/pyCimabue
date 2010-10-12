'''
Created on 14 Sep 2009

@author: piero
'''

import zmq
import pickle
import logging
#from utilities.nullHandler import *

class Message:

    def __init__(self, priority=2):
        self.type = self.__class__.__name__
        self.priority = priority
        self.address = ''
        self.data = ''

        # Logging
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
        self.logger = logging.getLogger('ActiveObject')
        self.logger.setLevel(logging.DEBUG)
        #h = NullHandler()
        #self.logger.addHandler(h)
        

    def __str__(self):
        msg = '[' + self.type + ']\n'
        msg = msg + '\tP: ' + str(self.priority) + '\n'
        msg = msg + '\tA: ' + self.address + '\n'
        msg = msg + '\tD: ' + self.data + '\n'
        return msg


    def msg2dict(self):
        msg_dict = {'t': self.type}
        msg_dict['p'] = self.priority
        msg_dict['a'] = self.address
        msg_dict['d'] = self.data
        return msg_dict
    
    
    def dict2msg(self, msg_dict):
        self.type = msg_dict['t']
        self.priority = msg_dict['p']
        self.address = msg_dict['a']
        self.data = msg_dict['d']


    def send(self, skt):
        skt.send_pyobj(pickle.dumps(self.msg2dict()))
        #self.logger.debug("[ ] Sent: " + str(self))
        
        # Receive reply
        if skt.socket_type == zmq.REQ or skt.socket_type == zmq.XREP or skt.socket_type == zmq.PAIR:
            raw_data = ''
            try:
                raw_data = skt.recv_pyobj()
            
            except zmq.ZMQError:
                self.logger.error("[ERROR] Message.send()")
                self.type = ErrorMessage
                return None
                
            self.dict2msg(pickle.loads(raw_data))
            return self
        

    def recv(self, skt):
        raw_data = ''
    
        try:
            raw_data = skt.recv_pyobj()
        except zmq.ZMQError:
            self.logger.error("[ERROR] Message.recv()")
        
        msg_dict = pickle.loads(raw_data)
        self.dict2msg(msg_dict)


    def reply(self, skt):
        try:
            skt.send_pyobj(dumps(self.msg2dict()))
            #self.logger.debug("[ ] Replied: " + str(self))
        except zmq.ZMQError:
            self.logger.error("[ERROR] Message.reply()")


# Subclasses (message types)

class ConnectMessage(Message):
    pass
    
class SendMessage(Message):
    pass

class AddClientMessage(Message):
    pass

class PingMessage(Message):
    pass

class ErrorMessage(Message):
    pass

# Server registration
class HelloMessage(Message):
    pass

class WelcomeBackupMessage(Message):
    pass

class WelcomeIdleMessage(Message):
    pass

# Server synchronization
class SyncServerListMessage(Message):
    pass

class SyncClientListMessage(Message):
    pass

# Server update
class BecomeMasterMessage(Message):
    pass

class BecomeBackupMessage(Message):
    pass

class NewMasterMessage(Message):
    pass
