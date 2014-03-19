from scrapy import log
from myfuncs import *

class URL(object):

	def __init__(self, url, scrapeid, long_count, parent=None, base=None):
		self.original = url
		if parent:
			protocol = parent.protocol
			subdomain = parent.subdomain
			domain = parent.domain
		elif base:
			protocol = base['protocol']
			subdomain = base['subdomain']
			domain = base['domain']
		else:
			protocol = "error"
			subdomain = "error"
			domain = "error"
		
		self.scrapeid = scrapeid
		
		self.domain = domain
		
		if not subdomain:
			subdomain = "www."
		
		url = self.set_protocol(url, protocol)
		
		url = self.set_subdomain(url, domain, subdomain)
		
		self.set_path(url)
		
		self.parents = self.get_parents(url.split("/"), [], 0)
		
		self.full = self.protocol + self.subdomain + self.domain + self.path
		
		#self.name = self.get_name(self.subdomain, self.path)
		self.name, self.long_count = filename_safe(self.full, long_count)
		
		
	def set_path(self, url):
		pos = url.find("#")
		if pos > -1:
			url = url[:pos]
		
		if url and url[-1] == "/":
				url = url[:-1]
		
		self.path = url
	
	def get_parents(self, path_list, parents_list, n):
		if n == 0:
			new_path_list = []
			for x in path_list:
				if x != "":
					new_path_list.append(x)
		else:
			new_path_list = path_list
		
		length = len(new_path_list)
		if length > 1:
			parents_list.append([self.scrapeid, self.subdomain + self.domain + "/" + "/".join(new_path_list[:length-1]), self.subdomain + self.domain + "/" + "/".join(new_path_list)])
			self.get_parents(new_path_list[:length-1], parents_list, n+1)
		elif length == 1:
			parents_list.append([self.scrapeid, self.domain, self.subdomain + self.domain + "/" + new_path_list[0]])
			#parents_list.append([self.scrapeid, "All", self.domain])
		return parents_list
	
	def set_domain(self, url, domain):
		pos = url.find("/")
		if pos == 0:
			self.domain = domain
			return url
		elif pos == -1:
			self.domain = url
			return ""
		else:
			self.domain = url[:pos]
			return url[pos:]
	
	def set_subdomain_old(self, url, subdomain):
		slash = url.find("/")
		dot = url.find(".")
		dot2 = url[dot+1:].find(".")
		if dot2 > -1 and dot2 < slash:
			self.subdomain = url[:dot+1]
			return url[dot+1:]
		else:
			self.subdomain = subdomain
			return url
	
	def set_subdomain(self, url, domain, subdomain):
		pos = url.find(domain)
		if pos == -1:
			self.domain = ""
			self.subdomain = subdomain
			return url
		elif pos == 0:
			self.subdomain = subdomain
			return url[len(domain):]
		else:
			self.subdomain = url[:pos]
			return url[pos + len(domain):]
	
	def set_protocol(self, url, protocol):
		pos = url.find("//")
		if pos == -1:
			self.protocol = protocol
		else:
			self.protocol = url[:pos+2]
			url = url[pos+2:]
		return url
	
	def get_name(self, subdomain, path):
		path = self.strip_bad_file_chars(self.replace_slashes(self.strip_outer_slashes(path),"--"))
		if path:
			return subdomain + self.domain + "--" + path
		else:
			return self.domain
	
	def strip_bad_file_chars(self, string):
		bad_chars = ["?", "\\", '"', ":", "*", "<", ">", "|"]
		for char in bad_chars:
			if char in string:
				string = string.replace(char, "-")
		return string
	
	def strip_outer_slashes(self, string):
		if string:
			if string[0] == "/":
				string = string[1:]
			#if len(string) == 0:
			#	return "root_page"
			if string[-1] == "/":
				string = string[:-1]
			#if len(string) == 0:
			#	return "root_page"
		return string
	
	def replace_slashes(self, string, new):
		if "/" in string:
			pos = string.find("/")
			return self.replace_slashes(string[:pos] + new + string[pos+1:],new)
		else:
			return string