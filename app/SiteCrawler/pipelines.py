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

class CsvExportPipeline(object):

	def __init__(self):
		self.files = {}
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
		nodes = open(getcwd()+r'\nodes.csv', 'w+b')
		self.files[spider] = nodes
		self.exporter1 = CsvItemExporter(nodes, fields_to_export=['url','name','screenshot'])
		self.exporter1.start_exporting()
		
		self.edges = []
		self.edges.append(['Source','Target','Type','ID','Label','Depth','Level','Weight'])
		self.num = 1
		
		self.parents = []
		self.parents.append(['Parent','Child'])
	
	def spider_closed(self, spider):
		self.exporter1.finish_exporting()
		file = self.files.pop(spider)
		file.close()
		
		writeCsvFile(getcwd()+r'\edges.csv', self.edges)
		writeCsvFile(getcwd()+r'\parents.csv', self.parents)
	
	def process_item(self, item, spider):
		self.exporter1.export_item(item)
		
		if item['url_obj'].full not in self.urls_seen:
			self.urls_seen.add(item['url_obj'].full)
		
		if self.depth == -1:
			self.depth = 0
		elif item['depth'] != self.depth:
			self.depth = item['depth']
			for link in self.holding:
				self.completed_depth.append(link)
			self.holding = []
		
		for link in item['links']:
			self.holding.append(link.full)
			if link.full in self.completed_depth:
				level = "secondary"
			else:
				level = "primary"
			self.edges.append([item['url_obj'].full.encode('utf-8'),link.full.encode('utf-8'),'Directed',self.num,'',self.depth,level,1])
			self.num += 1
		
		for tup in item['url_obj'].parents:
			if tup not in self.parents:
				self.parents.append(tup)
		
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
		self.conn = sqlite3.connect('sitecrawler.db')
		self.c = self.conn.cursor()
		self.node_tups = set()
		self.edge_tups = set()
		self.parent_tups = []
	
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
		
		scrapeid = list(self.edge_tups)[0][0]
		results = select_from(self.c, "SELECT domain, date FROM scrapes WHERE id = ?", scrapeid)
		domain, date = results[0]
		
		parents_dict = {}
		parents_dict["name"] = domain
		parents_dict["children"] = get_children(self.c, domain, scrapeid)

		with open(r'{0}\initiator\static\scrapes\{1}\{2}\sitemap.json'.format(getcwd(), domain, date), 'w') as outfile:
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
		
		return item