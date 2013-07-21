import csv
from urllib2 import urlopen

def get_name(url, root):
	pos = url.find(root)
	if pos + 1:
		if len(url) <= pos + len(root):
			return "root_page"
		else:
			return strip_inner_slashes(strip_outer_slashes(url[pos + len(root):]))
	else:
		return "root_not_found"

def strip_outer_slashes(string):
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

def strip_inner_slashes(string):
	if "/" in string:
		pos = string.find("/")
		return strip_inner_slashes(string[:pos] + "--" + string[pos+1:])
	else:
		return string

def url_fix(root, url):
	if root not in url:
		if "http" in url:
			return False
		url = root + url
	return add_slash(de_hash(url))

def de_hash(url):
	if '#' in url:
		pos = url.find('#')
		return url[:pos]
	else:
		return url

def writeCsvFile(fname, data, *args, **kwargs):
    """
    @param fname: string, name of file to write
    @param data: list of list of items

    Write data to file
    """
    mycsv = csv.writer(open(fname, 'wb'), *args, **kwargs)
    for row in data:
        mycsv.writerow(row)

def insert_row(connection, statement, items):
	try:
		connection.execute(statement, items)
	except Exception, e:
		print "Insert failed: %s" % e
		log.msg('-------------------------   INSERT FAILED   --------------------------')
		log.msg("Insert failed: %s" % e)

def strip_www(url):
	pos = url.find("www.")
	if pos >= 0:
		return url[pos+4:]

def test_url(url):
	try:
		code = urlopen('http://' + url).code
	except:
		return False
	if (code / 100 >= 4):
		return False
	else:
		return True

def add_slash(url):
	if url[-1] == "/":
		return url
	else:
		return url + "/"