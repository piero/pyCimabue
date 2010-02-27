#!/usr/bin/env python

'''
Created on Dec 14, 2009

@author: piero
'''

import pygtk
pygtk.require('2.0')
import gtk

import gobject
import threading
from listener import *
from clientProxy import *

# Allow other threads to run
gobject.threads_init()


class ClientInterface:
    
    def addClientCallback(self, client=None):
        self.clientList.append([client])
        
    def clearClientListCallback(self):
        self.clientList.clear()
    
    def sendCallback(self, widget, data=None):
        text = self.textInputBuffer.get_text(self.textInputBuffer.get_start_iter(),
                                      self.textInputBuffer.get_end_iter(),
                                      include_hidden_chars=False)
        # Delete text from the input box
        self.textInputBuffer.set_text('')
        
        # Ignore empty text 
        if text == '':
            return
        
        destination = None
        reply = None
        
        if len(self.clientList) > 0:
            (model, model_iter) = self.listView.get_selection().get_selected()
            destination = model.get(model_iter, 0)[0]
            print "Sending \"%s\" to  %s" % (text, destination)
        
        if destination is not None:
            reply = self.client.send_message(destination, text)
        
        if reply is not None:
            self.print_message("> %s: %s" % (destination, text))

    
    def delete_event(self, widget, event, data=None):
        print "Bye :)"
        self.__destroy_client()
        gtk.main_quit()
        
    
    def __destroy_client(self):
        if self.listener != None:
            self.listener.stop()
            self.listener.join(2.0)
            self.listener = None
        
        if self.client != None:
            self.client.kill()
            self.client = None
    
    
    def __create_new_client(self, widget, data=None):
        if self.client != None:
            self.__destroy_client()
            
        widget.set_sensitive(False)
        address = self.addressField.get_text()
        port = self.portField.get_text()
        
        if address == None or port == None:
            self.set_status("ERROR: Invalid address or port")
        else:
            print "Creating new client %s:%s..." % (address, port)
            self.client = ClientProxy(address, int(port))
            self.client.logger.setLevel(logging.DEBUG)
            self.client.interface = self
            
            self.listener = Listener(executioner=self.client,
                                     host=address,
                                     port=int(port))
            self.listener.start()
            connected = self.client.connect()
            
            if connected:
                self.window.set_title("ClientProxy [%s]" % self.client.get_name())
            else:
                self.set_status("ERROR: No server found")
                self.__destroy_client()
                widget.set_sensitive(True)
    
    
    def print_message(self, msg):
        if msg != None:
            iter = self.textOutputBuffer.get_end_iter()
            self.textOutputBuffer.insert(iter, "%s\n" % msg)
    
    
    def set_status(self, msg):
        if msg != None:
            self.statusBar.push(self.context_id, msg)
        
    
    def __init__(self):
        self.client = None
        self.listener = None
        
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
        
        connectButton = gtk.Button("Connect")
        connectButton.connect("clicked", self.__create_new_client)
        connectButton.show()
        
        addressBox = gtk.HBox(False, 0)
        addressBox.pack_start(addressLabel, True, True, 0)
        addressBox.pack_start(self.addressField, True, True, 10)
        addressBox.pack_start(portLabel, True, True, 10)
        addressBox.pack_start(self.portField, True, True, 10)
        addressBox.pack_start(connectButton, True, True, 10)
        addressBox.show()
        
        # Text output field
        textOutput = gtk.TextView()
        textOutput.set_wrap_mode(gtk.WRAP_WORD)
        textOutput.set_editable(False)
        textOutput.show()
        self.textOutputBuffer = textOutput.get_buffer()
        
        # Text output label
        textOutputLabel = gtk.Label("Conversation")
        textOutputLabel.show()
        
        # Text output scroll
        textOutputScroll = gtk.ScrolledWindow()
        textOutputScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textOutputScroll.add(textOutput)
        textOutputScroll.show()
        
        # Text output box
        textOutputBox = gtk.VBox(False, 0)
        textOutputBox.pack_start(textOutputLabel, True, True, 10)
        textOutputBox.pack_start(textOutputScroll, True, True, 10)
        textOutputBox.show()
        
        # Text input label
        textInputLabel = gtk.Label("Message to send")
        textInputLabel.show()
        
        # Text input field
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
        
        # Text input box
        textInputBox = gtk.VBox(False, 0)
        textInputBox.pack_start(textInputLabel, True, True, 0)
        textInputBox.pack_start(textInputScroll, True, True, 10)
        textInputBox.show()
        
        # Send button
        self.sendButton = gtk.Button("Send")
        self.sendButton.connect("clicked", self.sendCallback)
        self.sendButton.show()
        buttonBox = gtk.HBox(False, 0)
        buttonBox.pack_start(self.sendButton, True, True, 0)
        buttonBox.show()
        
        # Status bar
        self.statusBar = gtk.Statusbar()
        self.statusBar.show()
        self.context_id = self.statusBar.get_context_id("Statusbar")
        
        # Outer box
        outerBox = gtk.VBox(False, 0)
        outerBox.pack_start(addressBox, True, True, 0)
        outerBox.pack_start(textOutputBox, True, True, 10)
        outerBox.pack_start(textInputBox, True, True, 10)
        outerBox.pack_start(buttonBox, True, True, 10)
        outerBox.pack_start(self.statusBar, True, True, 10)
        outerBox.show()

        # ClientProxy list
        self.clientList = gtk.ListStore(str)
        self.listView = gtk.TreeView(self.clientList)
        self.listView.set_headers_visible(True)
        self.listView.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.cell = gtk.CellRendererText()
        tvcolumn = gtk.TreeViewColumn("Clients", self.cell, text=0)
        tvcolumn.set_resizable(True)
        #tvcolumn.pack_start(self.cell, True)
        tvcolumn.add_attribute(self.cell, 'text', 0)
        self.listView.append_column(tvcolumn)
        self.listView.show()

        # Main box
        mainBox = gtk.HBox(False, 0)
        mainBox.pack_start(outerBox)
        mainBox.pack_end(self.listView)
        mainBox.show()
        
        self.window.add(mainBox)
        self.window.set_title("ClientProxy [Not connected]")
        self.window.show()
    
    
    def main(self):
        gtk.main()


### EXECUTION STARTS HERE ###
if __name__ == "__main__":
    hello = ClientInterface()
    hello.main()
