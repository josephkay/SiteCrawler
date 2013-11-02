# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html
from os import getcwd
import sqlite3
import json
from screenshooter import Screenshooter
from scrapy.exceptions import DropItem
from scrapy import signals
from scrapy.contrib.exporter import CsvItemExporter
from spiders.myfuncs import *
from scrapy import log

class SitecrawlerPipeline(object):
	def process_item(self, item, spider):
		return item

class DuplicatesPipeline(object):
	
	def __init__(self):
		self.urls_seen = set()
	
	def process_item(self, item, spider):
		if item['url_obj'].full in self.urls_seen:
			raise DropItem("Duplicate item found: %s" % item)
		else:
			self.urls_seen.add(item['url_obj'].full)
			return item

class ScreenshotPipeline(object):
	
	def __init__(self):
		self.s = Screenshooter()
	
	def process_item(self, item, spider):
		self.s.capture(item['url_obj'].full, r"{0}\initiator\static\scrapes\{1}\{2}\{3}.png".format(getcwd(), item['scrape_domain'], item['date'], item['url_obj'].name))
		return item

class TextAnalysisPipeline(object):
	
	def __init__(self):
		pass
	
	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline
	
	def spider_opened(self, spider):
		self.conn = sqlite3.connect(db_file)
		self.c = self.conn.cursor()
		self.sentences = []
		self.words = []
		self.scrapeid = None
		self.date = None
		self.domain = None
	
	def spider_closed(self, spider):
		insert_rows(self.c, "INSERT INTO words (scrapeid, url, word, freq) VALUES (?, ?, ?, ?)", self.words)
		insert_rows(self.c, "INSERT INTO sentences (scrapeid, url, sentence) VALUES (?, ?, ?)", self.sentences)
		
		
		
		urls = select_from(self.c, "SELECT url FROM nodes WHERE scrapeid = ?", self.scrapeid)
		words = select_from(self.c, "SELECT url, word, freq FROM words WHERE scrapeid = ?", self.scrapeid)
		sentences = select_from(self.c, "SELECT url, sentence FROM sentences WHERE scrapeid = ?", self.scrapeid)
		url_word_count = select_from(self.c, "SELECT url, SUM(freq) FROM words WHERE scrapeid = ? GROUP BY url", self.scrapeid)
		url_sentence_count = select_from(self.c, "SELECT url, COUNT(*) FROM sentences WHERE scrapeid = ? GROUP BY url", self.scrapeid)
			
		sentences = [[url, sent, 1] for [url, sent] in sentences]

		url_stats = {"Total":{"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}, "urls":{}}
		w_group_size = 1
		s_group_size = 5
		longest_word = 1
		longest_sent = 1

		for [url] in urls:
			if url not in url_stats["urls"]:
				url_stats["urls"][url] = {"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}

		for url, word, freq in words:
			if real_word(word):
				length = len(word)
				if length > longest_word:
					longest_word = length

		for url, sent, freq in sentences:
			length = sentence_length(sent)
			if length > longest_sent:
				longest_sent = length

		def get_label_refs(longest, group_size):
			group_range = range(1, int(math.ceil(longest/float(group_size))+1))
			label_refs = {}
			for group_no in group_range:
				low_end = (int(group_no)-1)*group_size+1
				high_end = int(group_no)*group_size
				if low_end == high_end:
					label = "{0}".format(low_end)
				else:
					label = "{0} - {1}".format(low_end, high_end)
				label_refs[label] = range(low_end,high_end+1)
				labels = [label for label, lengths in sorted(label_refs.iteritems(), key=itemgetter(1))]
			return label_refs, labels
			
		w_label_refs, w_labels = get_label_refs(longest_word, w_group_size)
		s_label_refs, s_labels = get_label_refs(longest_sent, s_group_size)

		def add_labels_lengths(label_refs, type, url):
			for label in label_refs:
				url_stats["urls"][url]["length"][type]["labels"][label] = {}
				for length in label_refs[label]:
					url_stats["urls"][url]["length"][type]["labels"][label][length] = {"freq":0, "items":[]}

		for url in urls:
			add_labels_lengths(w_label_refs, "word", url[0])
			add_labels_lengths(s_label_refs, "sent", url[0])

		for label in w_label_refs:
			url_stats["Total"]["length"]["word"]["labels"][label] = {}
			for length in w_label_refs[label]:
				url_stats["Total"]["length"]["word"]["labels"][label][length] = {"freq":0, "items":[]}
				
		for label in s_label_refs:
			url_stats["Total"]["length"]["sent"]["labels"][label] = {}
			for length in s_label_refs[label]:
				url_stats["Total"]["length"]["sent"]["labels"][label][length] = {"freq":0, "items":[]}

		def add_freqs_words(items_list, type, label_refs, length_func=None, validate_func=None):
			for url, item, freq in items_list:
				#print "{0}: {1} - {2}".format(url, item.encode("ascii", errors="ignore"), freq)
				# Remove this and put sentence filter in to remove "." further upstream
				if type == "sent" and len(item) <= 1:
					continue
				if validate_func:
					if not validate_func(item):
						continue
				
				if length_func:
					length = length_func(item)
				else:
					length = len(item)
				if length == 0:
					continue
				
				for lab, lengths in label_refs.iteritems():
					if length in lengths:
						label = lab
						continue
				
				url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"] += freq
				url_stats["urls"][url]["length"][type]["labels"][label][length]["items"].append(item)
				
				url_stats["Total"]["length"][type]["labels"][label][length]["freq"] += freq
				if item not in url_stats["Total"]["length"][type]["labels"][label][length]["items"]:
					url_stats["Total"]["length"][type]["labels"][label][length]["items"].append(item)

		add_freqs_words(words, "word", w_label_refs, validate_func=real_word)
		add_freqs_words(sentences, "sent", s_label_refs, length_func=sentence_length)

		for type in ["word", "sent"]:

			for url in url_stats["urls"]:
				total = 0
				count = 0
				for label, lengths in url_stats["urls"][url]["length"][type]["labels"].iteritems():
					for length in lengths:
						freq = url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"]
						total += length*freq
						count += freq
						#print "length: {0}, freq: {1}".format(length, freq)
				if count == 0:
					url_stats["urls"][url]["length"][type]["average"] = 0
				else:
					url_stats["urls"][url]["length"][type]["average"] = total/float(count)
			
			total = 0
			count = 0
			for label, lengths in url_stats["Total"]["length"][type]["labels"].iteritems():
				for length in lengths:
					freq = url_stats["Total"]["length"][type]["labels"][label][length]["freq"]
					total += length*freq
					count += freq
			if count == 0:
				url_stats["Total"]["length"][type]["average"] = 0
			else:
				url_stats["Total"]["length"][type]["average"] = total/float(count)
		
		name_url_dict = {}
		long_count = 0
		
		for url in url_stats["urls"]:
			name = url.replace("/", "-")
			for char in [":","<",">","?","\"","*","."]:
				name = name.replace(char, "")
			if len(name) > 100:
				name = name[:80] + "---#" + str(long_count)
				long_count += 1
			with open(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, name), 'w') as outfile:
				json.dump(url_stats["urls"][url], outfile)
			name_url_dict[name] = url
		
		save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, name_url_dict), name_url_dict)
		save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, w_labels), w_labels)
		save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, s_labels), s_labels)
		
		
		self.conn.commit()
		self.conn.close()
	
	def process_item(self, item, spider):
		for sentence in item['sentences']:
			self.sentences.append((item['scrapeid'], item['url_obj'].full, sentence))
			
		for word, freq in item['words'].iteritems():
			self.words.append((item['scrapeid'], item['url_obj'].full, word, freq))
		
		if not self.scrapeid or not self.date or not self.domain:
			self.scrapeid = item['scrapeid']
			self.date = item['date']
			self.domain = item['url_obj'].domain
		
		return item

class SQLiteExportPipeline(object):

	def __init__(self):
		self.urls_seen = set()
		self.depth = -1
		self.holding = []
		self.completed_depth = []
	
	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline

	def spider_opened(self, spider):
		self.conn = sqlite3.connect(db_file)
		self.c = self.conn.cursor()
		self.node_tups = set()
		self.edge_tups = set()
		self.parent_tups = []
		self.scrapeid = None
		self.date = None
		self.domain = None
	
	def spider_closed(self, spider):
		insert_rows(self.c, "INSERT INTO nodes (id, scrapeid, url, name, social) VALUES (?, ?, ?, ?, ?)", list(self.node_tups))
		
		new_edge_tups = []
		nlen = len(self.edge_tups)
		n = 0
		for [scrapeid, source_url, target_url, level] in self.edge_tups:
			try:
				sourceid = select_from_and(self.c, "SELECT id FROM nodes WHERE url = ? AND scrapeid = ?", source_url, scrapeid)[0][0]
				targetid = select_from_and(self.c, "SELECT id FROM nodes WHERE url = ? AND scrapeid = ?", target_url, scrapeid)[0][0]
				new_edge_tups.append((scrapeid, sourceid, targetid, level))
			except Exception, e:
				n += 1
				log.msg('-------------------------   SELECT FAILED   --------------------------')
				log.msg("Select failed: {0} --- failure: {1}/{2}".format(e, n, nlen))
		
		insert_rows(self.c, "INSERT INTO edges (scrapeid, sourceid, targetid, level) VALUES (?, ?, ?, ?)", new_edge_tups)
		insert_rows(self.c, "INSERT INTO parents (scrapeid, parent, child) VALUES (?, ?, ?)", self.parent_tups)
		
		parents_dict = {}
		parents_dict["name"] = self.domain
		parents_dict["children"] = get_children(self.c, self.domain, self.scrapeid)

		with open(r'{0}\initiator\static\scrapes\{1}\{2}\sitemap.json'.format(getcwd(), self.domain, self.date), 'w') as outfile:
			json.dump(parents_dict, outfile)
		
		self.conn.commit()
		self.conn.close()
	
	def process_item(self, item, spider):
		if item['url_obj'].full not in self.urls_seen:
			self.urls_seen.add(item['url_obj'].full)
		
		if self.depth == -1:
			self.depth = 0
		elif item['depth'] != self.depth:
			self.depth = item['depth']
			for link in self.holding:
				self.completed_depth.append(link)
			self.holding = []
		
		self.node_tups.add((None, item['scrapeid'], item['url_obj'].full, item['url_obj'].name, item['social']))
		
		for link in item['links']:
			self.holding.append(link.full)
			if link.full in self.completed_depth:
				level = 2
			else:
				level = 1
			self.edge_tups.add((item['scrapeid'], item['url_obj'].full, link.full, level))
		
		if not item['social']:
			for tup in item['url_obj'].parents:
				if tup not in self.parent_tups:
					self.parent_tups.append(tup)
		
		if not self.scrapeid or not self.date or not self.domain:
			self.scrapeid = item['scrapeid']
			self.date = item['date']
			self.domain = item['url_obj'].domain
		
		return item