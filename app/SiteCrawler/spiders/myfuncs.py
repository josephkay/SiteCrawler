import csv
from urllib2 import urlopen
from scrapy import log
from PIL import Image
from BeautifulSoup import BeautifulSoup
import re
from nltk.tokenize import sent_tokenize
from nltk.corpus import cmudict
from nltk.tokenize import RegexpTokenizer
from HTMLParser import HTMLParser
import json
from selenium import webdriver

db_file = "sitecrawlerdb.db"

def screenshot(url, output_path):
	driver = webdriver.PhantomJS(executable_path=r'C:\Users\kayj\AppData\Roaming\npm\node_modules\phantomjs\lib\phantom\phantomjs')
	#driver.set_window_size(1024, 768) # optional
	driver.get(url)
	driver.save_screenshot(output_path) # save a screenshot to disk

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

def make_csv_sitemap(csv_file, trees_list, depth):
	for tree in trees_list:
		url = tree['url']
		
		row = [""]*depth
		row.append(url)
		csv_file.writerow(row)
		
		if "children" in tree:
			children = tree['children']
			csv_file = make_csv_sitemap(csv_file, children, depth+1)
	
	return csv_file

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

def get_children(connection, parent, scrapeid, url_names_dict):
	dict_list = []
	children = select_from_and(connection, "SELECT child FROM parents WHERE parent = ? and scrapeid = ?", parent, scrapeid)
	for [url] in children:
		if url in url_names_dict:
			name = url_names_dict[url].encode('utf-8')
		else:
			name = ""
		url = url.encode('utf-8')
		dict = {}
		dict["url"] = url
		dict["name"] = name
		children_list = get_children(connection, url, scrapeid, url_names_dict)
		if children_list:
			dict["children"] = children_list
		dict_list.append(dict)
	return dict_list

def timeout(func, args=(), kwargs={}, timeout_duration=10, default=None):
    """This function will spawn a thread and run the given function
    using the args, kwargs and return the given default value if the
    timeout_duration is exceeded.
    """ 
    import threading
    class InterruptableThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = default
        def run(self):
            self.result = func(*args, **kwargs)
    it = InterruptableThread()
    it.start()
    it.join(timeout_duration)
    if it.isAlive():
        return it.result
    else:
        return it.result

### --- text manipulation functions --- ###

def filename_safe(url, long_count):
	loc = url.find("//")
	if loc != -1:
		url = url[loc+2:]
	name = url.replace("/", "-")
	for char in [":","<",">","?","\"","*"]:
		name = name.replace(char, "")
	if len(name) > 100:
		name = name[:80] + "---#" + str(long_count)
		long_count += 1
	return name, long_count

def ignore_tags(soup, tags_list):
	for tag in tags_list:
		tags = soup.findAll(tag)
		for t in tags:
			if t.string:
				t.replaceWith(t.string)
			else:
				t.replaceWith("")
	return BeautifulSoup(str(soup))

def replace_bad_chars(text):

	text = text.decode("utf-8")
	
	char_replacements = [
    ( u'\u2018', u"'"),   # LEFT SINGLE QUOTATION MARK
    ( u'\u2019', u"'"),   # RIGHT SINGLE QUOTATION MARK
    ( u'\u201c', u'"'),   # LEFT DOUBLE QUOTATION MARK
    ( u'\u201d', u'"'),   # RIGHT DOUBLE QUOTATION MARK
    ( u'\u201e', u'"'),   # DOUBLE LOW-9 QUOTATION MARK
    ( u'\u2013', u'-'),   # EN DASH
    ( u'\u2026', u'...'), # HORIZONTAL ELLIPSIS
    ( u'\u0152', u'OE'),  # LATIN CAPITAL LIGATURE OE
    ( u'\u0153', u'oe'),  # LATIN SMALL LIGATURE OE
	( u'\u00B7', u''),    # MIDDLE DOT
	( u"\u2022", u'') ]   # BULLET
	
	for (bad, good) in char_replacements:
		text = text.replace(bad, good)
	return text

def get_texts(url):
	html = urlopen(url).read()
	html = replace_bad_chars(remove_comments(html))
	soup = BeautifulSoup(html)
	soup = ignore_tags(soup, ['b', 'i', 'u', 'a', 'span'])
	return soup.findAll(text=True)

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True

def sentence(element):
	sentence_chars = [".","!","?"]
	for char in sentence_chars:
		if element and element[-1] == char:
			return True
	return False

def length(element):
	if len(word_split([element])) < 2:
		return False
	return True

def filters(filter_list, texts):
	for f in filter_list:
		texts = filter(f, texts)
	return texts

def sentence_split(text_list):
	new_list = []
	for text in text_list:
		sents = sent_tokenize(text)
		for sent in sents:
			new_list.append(sent)
	return new_list

def word_split(text_list):
	tokenizer = RegexpTokenizer(r'[,:;/\s+]', gaps=True)
	new_dict = {}
	for text in text_list:
		for word in tokenizer.tokenize(text):
			paren_a = word.find("(")
			paren_b = word.find(")")
			if paren_a > 0 and paren_b == len(word):
				word = word[:paren_a] + word[paren_a+1:paren_b]
			word = word.lower().strip('\'\"-_,.:;!?()*\\/[]{}|<>~=')
			if word:
				if word in new_dict:
					new_dict[word] += 1
				else:
					new_dict[word] = 1
	return new_dict

def syllables(text_list):
	d = cmudict.dict()
	tokenizer = RegexpTokenizer(r'\w+')
	new_set = set()
	error_count = 0
	s_list = []
	for text in text_list:
		for word in tokenizer.tokenize(text):
			try:
				syllables = [len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]]
				s_list.append(float(syllables[0]))
			except:
				syllables = (-1,)
				error_count += 1
			new_set.add((word, syllables[0]))
	return list(new_set), error_count, sum(s_list)/len(s_list)

def sentence_length(sentence):
	tokenizer = RegexpTokenizer(r'\w+')
	return len(tokenizer.tokenize(sentence))

class MLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		self.fed, output = [], self.fed
		return ''.join(output)

def strip_tags(texts):
	s = MLStripper()
	new_list = []
	for text in texts:
		s.feed(text)
		new_list.append(s.get_data())
	return new_list

def convert_entities(texts):
	h = HTMLParser()
	return [h.unescape(text) for text in texts]

def replace_breaks(texts):
	return [re.sub(r"\s+", " ", text) for text in texts]

def real_word(word):
	non_word_chars = [".","/","\\","_"]
	for char in non_word_chars:
		if char in word:
			return False
	return True

def remove_comments(html):
	while True:
		start = html.find("<!--")
		if start == -1:
			break
		end = html.find("-->", start)
		html = html[:start] + html[end+3:]
	return html
	
def save_json(location, object):
	with open(location, 'w') as outfile:
		json.dump(object, outfile)