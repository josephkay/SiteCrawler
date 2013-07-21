# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html
from os import getcwd
import sqlite3
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
		image_folder = "screenshots\\"
		self.s.capture(item['url'], image_folder + item['screenshot'])
		return item

class CsvExportPipeline(object):

	def __init__(self):
		self.files = {}
	
	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline

	def spider_opened(self, spider):
		nodes = open(getcwd()+r'\%s_nodes.csv' % spider.name, 'w+b')
		self.files[spider] = nodes
		self.exporter1 = CsvItemExporter(nodes, fields_to_export=['url','name','screenshot'])
		self.exporter1.start_exporting()
		
		self.edges = []
		self.edges.append(['Source','Target','Type','ID','Label','Weight'])
		self.num = 1
	
	def spider_closed(self, spider):
		self.exporter1.finish_exporting()
		file = self.files.pop(spider)
		file.close()
		
		writeCsvFile(getcwd()+r'\edges.csv', self.edges)
	
	def process_item(self, item, spider):
		self.exporter1.export_item(item)
		
		for url in item['links']:
			self.edges.append([item['url'],url,'Directed',self.num,'',1])
			self.num += 1
		return item

class SQLiteExportPipeline(object):

	def __init__(self):
		pass
	
	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline

	def spider_opened(self, spider):
		self.conn = sqlite3.connect('sitecrawler.db')
		self.c = self.conn.cursor()
	
	def spider_closed(self, spider):
		self.conn.commit()
		self.conn.close()
	
	def process_item(self, item, spider):
		insert_row(self.c, "INSERT INTO nodes (id, url, name, screenshot) VALUES (?, ?, ?, ?)", (None, item['url'], item['name'], item['screenshot']))
		
		for link in item['links']:
			insert_row(self.c, "INSERT INTO edges (id, source, target) VALUES (?, ?, ?)", (None, item['url'], link))
		return item