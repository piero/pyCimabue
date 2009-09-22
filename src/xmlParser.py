'''
Created on 21 Sep 2009

@author: piero
'''

from xml.dom import minidom


class XMLParser():
		
	def __init__(self, filename):
		self.__output_list = []
		self.xmldoc = minidom.parse(filename)
		# Populate output list
		self.__handle_server_list()

	def __del__(self):
		if self.xmldoc != None:
			self.xmldoc.unlink()
			
	def get_output_list(self):
		return self.__output_list


	# XML Parsing funcitons
	
	def __handle_server_list(self):
		servers = self.xmldoc.getElementsByTagName("server")
		self.__handle_servers(servers)

	def __handle_servers(self, servers):
		for s in servers:
			self.__handle_server(s)
			
	def __handle_server(self, server):
			ip = self.__handle_ip(server)
			port = self.__handle_port(server)
			#print "%s:%s" % (ip, port)
			self.__output_list.append((ip, port))

	def __handle_ip(self, server):
		ip = server.getElementsByTagName("ip")[0]
		return self.__get_text(ip.childNodes)
	
	def __handle_port(self, server):
		ip = server.getElementsByTagName("port")[0]
		return self.__get_text(ip.childNodes)
	
	def __get_text(self, nodelist):
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				return node.data