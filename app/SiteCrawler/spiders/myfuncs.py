import csv
from urllib2 import urlopen
from scrapy import log

def get_domain(url):
	pos = url.find(".")
	if url[pos+1:].find(".") > -1:
		url = url[pos+1:]
	
	pos = url.find("//")
	if pos > -1:
		url = url[pos+2:]
	
	pos = url.find("/")
	if pos > -1:
		url = url[:pos]
	
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
		log.msg("Insert ({0}) failed: {1}".format(statement, e))

def insert_rows(connection, statement, items):
	try:
		connection.executemany(statement, items)
	except Exception, e:
		print "Insert failed: %s" % e
		log.msg('-------------------------   INSERT FAILED   --------------------------')
		log.msg("Insert ({0}) failed: {1}".format(statement, e))

def select_from_and(connection, statement, where1, where2):
	try:
		connection.execute(statement, (where1, where2))
		return connection.fetchall()
	except Exception, e:
		print "Select failed: %s" % e
		log.msg('-------------------------   SELECT FAILED   --------------------------')
		log.msg("Select ({0}) failed: {1}".format(statement, e))

def select_from(connection, statement, where):
	try:
		connection.execute(statement, (where,))
		return connection.fetchall()
	except Exception, e:
		print "Select failed: %s" % e
		log.msg('-------------------------   SELECT FAILED   --------------------------')
		log.msg("Select ({0}) failed: {1}".format(statement, e))

def test_url(url):
	try:
		code = urlopen('http://' + url).code
	except:
		return False
	if (code / 100 >= 4):
		return False
	else:
		return True

def get_children(connection, parent, scrapeid):
	dict_list = []
	children = select_from_and(connection, "SELECT child FROM parents WHERE parent = ? and scrapeid = ?", parent, scrapeid)
	for tup in children:
		child = tup[0]
		dict = {}
		dict["name"] = child
		children_list = get_children(c, child, scrapeid)
		if children_list:
			dict["children"] = children_list
		dict_list.append(dict)
	return dict_list