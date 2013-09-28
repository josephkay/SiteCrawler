import csv
from urllib2 import urlopen
from scrapy import log
from PIL import Image

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
		child = tup[0].encode('utf-8')
		dict = {}
		dict["name"] = child
		children_list = get_children(connection, child, scrapeid)
		if children_list:
			dict["children"] = children_list
		dict_list.append(dict)
	return dict_list

def crop_image(image_path):
	img = Image.open(image_path)
	pixels = img.load()
	width, height = img.size
	row_height = get_blank_rows(None, height-1, width-1, pixels)
	if row_height+20 < height:
		new_img = img.crop((0,0,width,row_height+20))
		new_img.save(image_path)

def get_blank_rows(last_row, row_height, width, pixels):
	row = []
	for n in range(0, width+1, 10):
		row.append(pixels[n, row_height])
	if last_row == None or row == last_row:
		output = get_blank_rows(row, row_height-10, width, pixels)
	else:
		output = row_height
	return output