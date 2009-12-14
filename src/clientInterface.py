#!/usr/bin/env python

'''
Created on Dec 14, 2009

@author: piero
'''

import pygtk
pygtk.require('2.0')
import gtk

from listener import *
from client import *


class ClientInterface:
    
    def callback(self, widget, data=None):
        text = self.textInputBuffer.get_text(self.textInputBuffer.get_start_iter(),
                                      self.textInputBuffer.get_end_iter(),
                                      include_hidden_chars=False)
        print "Writing: %s" % text
        iter = self.textOutputBuffer.get_end_iter()
        self.textOutputBuffer.insert(iter, "%s\n" % text)
    
    
    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        gtk.main_quit()
        return False
    
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.set_border_width(10)

        self.outerBox = gtk.VBox(False, 0)
        
        # Text output
        self.textOutput = gtk.TextView()
        self.textOutput.set_wrap_mode(gtk.WRAP_WORD)
        self.textOutput.set_editable(False)
        self.textOutputBuffer = self.textOutput.get_buffer()
        
        # Text output scroll
        textOutputScroll = gtk.ScrolledWindow()
        textOutputScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textOutputScroll.add(self.textOutput)
        textOutputScroll.show()
        self.textOutput.show()
        
        self.outerBox.pack_start(textOutputScroll, True, True, 0)
        self.window.add(self.outerBox)
        
        # Text input
        self.textInput = gtk.TextView()
        self.textInput.set_wrap_mode(gtk.WRAP_WORD)
        self.textInput.set_editable(True)
        self.textInputBuffer = self.textInput.get_buffer()
        
        # Text input scroll
        textInputScroll = gtk.ScrolledWindow()
        textInputScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textInputScroll.add(self.textInput)
        textInputScroll.show()
        self.textInput.show()
        
        self.outerBox.pack_start(textInputScroll, True, True, 10)
        
        # Send button
        self.sendButton = gtk.Button("Send")
        self.sendButton.connect("clicked", self.callback)
        self.buttonBox = gtk.HBox(False, 0)
        self.buttonBox.pack_start(self.sendButton, True, True, 0)
        self.sendButton.show()
        
        self.outerBox.pack_start(self.buttonBox, True, True, 10)
        
        self.buttonBox.show()
        self.outerBox.show()
        self.window.show()
    
    
    def main(self):
        gtk.main()


### EXECUTION STARTS HERE ###
if __name__ == "__main__":
    hello = ClientInterface()
    hello.main()
