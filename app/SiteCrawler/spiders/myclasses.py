class URL(object):

	def __init__(self, url, parent=None, base=None):
		self.original = url
		if parent:
			protocol, subdomain, domain = parent.protocol, parent.subdomain, parent.domain
		elif base:
			protocol, subdomain, domain = base[protocol], base[subdomain], base[domain]
		else:
			protocol, subdomain, domain = "error", "error", "error"
		
		pos = url.find("//")
		if pos == -1:
				self.protocol = protocol
		else:
			self.protocol = url[:pos+2]
			url = url[pos+2:]

		
		pos = url.find(domain)
		if pos == -1:
			selfsubdomain = subdomain
			self.path = url
		else:
			if pos > 0:
				self.subdomain = url[:pos]
			else:
				self.subdomain = subdomain
			
			self.path = url[pos+len(domain):]