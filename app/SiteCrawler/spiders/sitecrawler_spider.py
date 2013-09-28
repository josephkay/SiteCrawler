from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from scrapy import log
from SiteCrawler.items import SiteCrawlerItem
from myfuncs import *
from myclasses import *
import sqlite3
import datetime
import calendar

class MySpider(CrawlSpider):
	name = 'SiteCrawler'
	rules = (
		## ---  "If multiple rules match the same link, the first one will be used, according to the order they're defined in this attribute."
		Rule(SgmlLinkExtractor(allow=("facebook\.com", "twitter\.com")), callback='social_parse', follow=False),
		Rule(SgmlLinkExtractor(allow=()), callback='main_parse', follow=True),
	)
	
	def __init__(self, root, date, **kwargs):
		#super(MySpider, self).__init__(*args, **kwargs)
		CrawlSpider.__init__(self, **kwargs)
		
		domain = get_domain(root)
		self.unix_date = date
		
		conn = sqlite3.connect('sitecrawler.db')
		c = conn.cursor()
		insert_row(c, "INSERT INTO scrapes (id, domain, date) VALUES (?, ?, ?)", (None, domain, self.unix_date))
		self.scrapeid = c.lastrowid
		log.msg("scrapeid = {0}".format(self.scrapeid))
		conn.commit()
		conn.close()
		
		self.seed = URL(root, self.scrapeid, base={'protocol':'http://', 'subdomain':'', 'domain':domain, 'path':''})
		#self.root = root
		self.start_urls = [self.seed.full]
		self.allowed_domains = [domain, "facebook.com", "twitter.com"]
	
	def parse_item(self, response, item):
		#self.urls_seen = set()
		#self.log('Hi, this is an item page! %s' % response.url)
		
		hxs = HtmlXPathSelector(response)
		#item = SiteCrawlerItem()
		#item['url_obj'] = URL(response.url, self.scrapeid, parent=self.seed)
		item['url'] = item['url_obj'].full
		item['name'] = item['url_obj'].name
		item['screenshot'] = item['name']+'.png'
		item['depth'] = response.meta['depth']
		item['links'] = []
		item['path'] = item['url_obj'].path 
		item['parents'] = item['url_obj'].parents
		item['scrapeid'] = self.scrapeid
		item['date'] = self.unix_date
		
		for url in hxs.select('//a/@href').extract():
			u = URL(url, self.scrapeid, parent=item['url_obj'])
			if u.domain:
				item['links'].append(u)
		return item
	
	def main_parse(self, response):
		item = SiteCrawlerItem()
		item['url_obj'] = URL(response.url, self.scrapeid, parent=self.seed)
		item['social'] = 0
		return self.parse_item(response, item)
	
	def social_parse(self, response):
		item = SiteCrawlerItem()
		if "facebook" in response.url:
			domain = "facebook.com"
		elif "twitter" in response.url:
			domain = "twitter.com"
		item['url_obj'] = URL(response.url, self.scrapeid, base={'protocol':'http://', 'subdomain':'www.', 'domain':domain, 'path':''})
		item['social'] = 1
		return self.parse_item(response)
	