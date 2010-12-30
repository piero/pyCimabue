'''
Created on 01/nov/2009

@author: piero
'''
import logging


class NullHandler(logging.Handler):
    '''
    classdocs
    '''


    def emit(self, record):
        pass
        