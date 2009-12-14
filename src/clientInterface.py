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
        addressLabel = gtk.Label("address")
        addressLabel.show()
        self.addressField = gtk.Entry(20)
        self.addressField.set_text("127.0.0.1")
        self.addressField.show()
        
        portLabel = gtk.Label("port")
        portLabel.show()
        self.portField = gtk.Entry(6)
        self.portField.set_text("24000")
        self.portField.show()
        addressBox = gtk.HBox(False, 0)
        addressBox.pack_start(addressLabel, True, True, 0)
        addressBox.pack_start(self.addressField, True, True, 10)
        addressBox.pack_start(portLabel, True, True, 0)
        addressBox.pack_start(self.portField, True, True, 10)
        addressBox.show()
        
        # Text output
        textOutput = gtk.TextView()
        textOutput.set_wrap_mode(gtk.WRAP_WORD)
        textOutput.set_editable(False)
        textOutput.show()
        self.textOutputBuffer = textOutput.get_buffer()
        
        textOutputLabel = gtk.Label("Received")
        textOutputLabel.show()
        
        # Text output scroll
        textOutputScroll = gtk.ScrolledWindow()
        textOutputScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textOutputScroll.add(textOutput)
        textOutputScroll.show()
        
        
        textOutputBox = gtk.VBox(False, 0)
        textOutputBox.pack_start(textOutputLabel, True, True, 10)
        textOutputBox.pack_start(textOutputScroll, True, True, 10)
        textOutputBox.show()
        
        
        textInputLabel = gtk.Label("Send")
        textInputLabel.show()
        
        # Text input
        textInput = gtk.TextView()
        textInput.set_wrap_mode(gtk.WRAP_WORD)
        textInput.set_editable(True)
        self.textInputBuffer = textInput.get_buffer()
        textInput.show()
        
        # Text input scroll
        textInputScroll = gtk.ScrolledWindow()
        textInputScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textInputScroll.add(textInput)
        textInputScroll.show()
        
        textInputBox = gtk.VBox(False, 0)
        textInputBox.pack_start(textInputLabel, True, True, 0)
        textInputBox.pack_start(textInputScroll, True, True, 10)
        textInputBox.show()
        
        # Send button
        self.sendButton = gtk.Button("Send")
        self.sendButton.connect("clicked", self.callback)
        self.sendButton.show()
        buttonBox = gtk.HBox(False, 0)
        buttonBox.pack_start(self.sendButton, True, True, 0)
        buttonBox.show()
        
        # Main box
        outerBox = gtk.VBox(False, 0)
        outerBox.pack_start(addressBox, True, True, 0)
        outerBox.pack_start(textOutputBox, True, True, 10)
        outerBox.pack_start(textInputBox, True, True, 10)
        outerBox.pack_start(buttonBox, True, True, 10)
        outerBox.show()
        
        self.window.add(outerBox)
        self.window.show()
    
    
    def main(self):
        gtk.main()


### EXECUTION STARTS HERE ###
if __name__ == "__main__":
    hello = ClientInterface()
    hello.main()
