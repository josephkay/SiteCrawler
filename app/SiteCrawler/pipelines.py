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
		if item['url'] in self.urls_seen:
			raise DropItem("Duplicate item found: %s" % item)
		else:
			self.urls_seen.add(item['url'])
			return item

class ScreenshotPipeline(object):
	
	def __init__(self):
		self.s = Screenshooter()
	
	def process_item(self, item, spider):
		self.s.capture(item['url'], r"{0}\scrapes\{1}\{2}\{3}.png".format(getcwd(), item['url_obj'].domain, item['date'], item['name']))
		#self.s.capture(item['url'], r"{0}\screenshots\{1}.png".format(getcwd(), item['name']))
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
		
		if item['url'] not in self.urls_seen:
			self.urls_seen.add(item['url'])
		
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
			self.edges.append([item['url'].encode('utf-8'),link.full.encode('utf-8'),'Directed',self.num,'',self.depth,level,1])
			self.num += 1
		
		for tup in item['parents']:
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
		insert_rows(self.c, "INSERT INTO nodes (id, scrapeid, url, name) VALUES (?, ?, ?, ?)", list(self.node_tups))
		
		new_edge_tups = []
		for [scrapeid, source_url, target_url, level] in self.edge_tups:
			try:
				sourceid = select_from_and(self.c, "SELECT id FROM nodes WHERE url = ? AND scrapeid = ?", source_url, scrapeid)[0][0]
				targetid = select_from_and(self.c, "SELECT id FROM nodes WHERE url = ? AND scrapeid = ?", target_url, scrapeid)[0][0]
				new_edge_tups.append((scrapeid, sourceid, targetid, level))
			except Exception, e:
				log.msg('-------------------------   INSERT FAILED   --------------------------')
				log.msg("Select failed: {0}".format(e))
		
		insert_rows(self.c, "INSERT INTO edges (scrapeid, sourceid, targetid, level) VALUES (?, ?, ?, ?)", new_edge_tups)
		insert_rows(self.c, "INSERT INTO parents (scrapeid, parent, child) VALUES (?, ?, ?)", self.parent_tups)
		
		scrapeid = list(self.edge_tups)[0][0]
		domain, date = select_from(self.c, "SELECT domain, date FROM scrapes WHERE scrapeid = ?", scrapeid)
		
		parents_dict = {}
		parents_dict["name"] = "root_page"
		parents_dict["children"] = get_children(c, "root_page", scrapeid)

		with open(r'{0}\scrapes\{1}\{2}\sitemap.json'.format(getcwd(), domain, date), 'w') as outfile:
			json.dump(dict, outfile)
		
		self.conn.commit()
		self.conn.close()
	
	def process_item(self, item, spider):
		if item['url'] not in self.urls_seen:
			self.urls_seen.add(item['url'])
		
		if self.depth == -1:
			self.depth = 0
		elif item['depth'] != self.depth:
			self.depth = item['depth']
			for link in self.holding:
				self.completed_depth.append(link)
			self.holding = []
		
		self.node_tups.add((None, item['scrapeid'], item['url'], item['name']))
		
		for link in item['links']:
			self.holding.append(link.full)
			if link.full in self.completed_depth:
				level = 2
			else:
				level = 1
			self.edge_tups.add((item['scrapeid'], item['url'], link.full, level))
		
		for tup in item['parents']:
			if tup not in self.parent_tups:
				self.parent_tups.append(tup)
		
		return item