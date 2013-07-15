import csv

def url_end(string):
	pos = string.find("/")
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

def url_fix(root, url):
	if root not in url:
		if "http" in url:
			return False
		url = root + url
	return de_hash(url)

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