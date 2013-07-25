class URL(object):

	def __init__(self, url, parent=None, base=None):
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
		
		self.domain = domain
		
		if not subdomain:
			subdomain = "www."
		
		url = self.set_protocol(url, protocol)
		
		url = self.set_subdomain(url, domain, subdomain)
		
		self.set_path(url)
		
		self.full = self.protocol + self.subdomain + self.domain + self.path
		
		self.name = self.get_name(self.subdomain, self.path)
	
	def set_path(self, url):
		pos = url.find("#")
		if pos > -1:
			url = url[:pos]
		
		if url and url[-1] == "/":
				url = url[:-1]
		
		self.path = url
	
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
		if not path:
			return "root_page"
		else:
			return subdomain[:-1] + "--" + self.replace_slashes(self.strip_outer_slashes(path),"--")
		
	def strip_outer_slashes(self, string):
		if string[0] == "/":
			string = string[1:]
		if len(string) == 0:
			return "root_page"
		if string[-1] == "/":
			string = string[:-1]
		if len(string) == 0:
			return "root_page"
		else:
			return string
	
	def replace_slashes(self, string, new):
		if "/" in string:
			pos = string.find("/")
			return self.replace_slashes(string[:pos] + new + string[pos+1:],new)
		else:
			return string