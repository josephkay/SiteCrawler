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
		log.msg("Insert failed: %s" % e)

def insert_rows(connection, statement, items):
	try:
		connection.executemany(statement, items)
	except Exception, e:
		print "Insert failed: %s" % e
		log.msg('-------------------------   INSERT FAILED   --------------------------')
		log.msg("Insert failed: %s" % e)

def test_url(url):
	try:
		code = urlopen('http://' + url).code
	except:
		return False
	if (code / 100 >= 4):
		return False
	else:
		return True