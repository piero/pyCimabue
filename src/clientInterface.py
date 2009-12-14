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
        # Delete text from the input box
        self.textInputBuffer.set_text('')
        
        print "Writing: %s" % text
        iter = self.textOutputBuffer.get_end_iter()
        self.textOutputBuffer.insert(iter, "%s\n" % text)
    
    
    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        gtk.main_quit()
        return False
    
    
    def print_message(self, msg):
        if msg != None:
            iter = self.textOutputBuffer.get_end_iter()
            self.textOutputBuffer.insert(iter, "%s\n" % msg)
    
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.set_border_width(10)

        # Address box
        self.addressField = gtk.Entry(20)
        self.addressField.set_text("127.0.0.1")
        self.addressField.show()
        self.portField = gtk.Entry(6)
        self.portField.set_text("24000")
        self.portField.show()
        self.addressBox = gtk.HBox(False, 0)
        self.addressBox.pack_start(self.addressField, True, True, 0)
        self.addressBox.pack_start(self.portField, True, True, 10)
        
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
        
        # Send button
        self.sendButton = gtk.Button("Send")
        self.sendButton.connect("clicked", self.callback)
        self.buttonBox = gtk.HBox(False, 0)
        self.buttonBox.pack_start(self.sendButton, True, True, 0)
        self.sendButton.show()
        
        # Main box
        self.outerBox = gtk.VBox(False, 0)
        self.outerBox.pack_start(self.addressBox, True, True, 0)
        self.outerBox.pack_start(textOutputScroll, True, True, 10)
        self.outerBox.pack_start(textInputScroll, True, True, 10)
        self.outerBox.pack_start(self.buttonBox, True, True, 10)
        
        self.window.add(self.outerBox)
        
        self.addressBox.show()
        self.buttonBox.show()
        self.outerBox.show()
        self.window.show()
    
    
    def main(self):
        gtk.main()


### EXECUTION STARTS HERE ###
if __name__ == "__main__":
    hello = ClientInterface()
    hello.main()
