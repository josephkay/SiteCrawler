def url_end(string):
	pos = string.find("/")
	print "string is: " + string
	print "pos is: " + str(pos)
	if pos+1:
		return url_end(string[pos+1:])
	else:
		return before_dot(string)

def before_dot(string):
	pos = string.find(".")
	if pos+1:
		return string[:pos]
	else:
		return string