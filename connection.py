from message import *
import threading


class Connection(threading.Thread):

    def __init__(self, client):
        self.client = client
        
    def run(self):
        # TODO: Send ping messages
        pass
