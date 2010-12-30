'''
Created on 26/set/2009

@author: piero
'''

from message import *
from utilities.pingAgent import *

class ServerStrategy:
    
    def __init__(self, server):
        self.__server = server


    def exit(self):
        pass