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
		self.scrape_domain = domain
		self.unix_date = date
		
		conn = sqlite3.connect(db_file)
		c = conn.cursor()
		insert_row(c, "INSERT INTO scrapes (id, domain, date) VALUES (?, ?, ?)", (None, domain, self.unix_date))
		self.scrapeid = c.lastrowid
		log.msg("scrapeid = {0}".format(self.scrapeid))
		conn.commit()
		conn.close()
		
		self.long_count = 0
		self.seed = URL(root, self.scrapeid, self.long_count, base={'protocol':'http://', 'subdomain':'', 'domain':domain, 'path':''})
		self.start_urls = [self.seed.full]
		self.allowed_domains = [domain, "facebook.com", "twitter.com"]
		self.long_count = self.seed.long_count
	
	def parse_item(self, response, item):
		
		log.msg("parse item")
		log.msg("URL: {0}".format(item['url_obj'].full))
		hxs = HtmlXPathSelector(response)
		item['depth'] = response.meta['depth']
		item['links'] = []
		item['scrapeid'] = self.scrapeid
		item['date'] = self.unix_date
		item['scrape_domain'] = self.scrape_domain
		
		#for url in hxs.select('//a/@href').extract():
		#	u = URL(url, self.scrapeid, parent=item['url_obj'])
		#	if u.domain:
		#		item['links'].append(u)
		
		visible_texts = filters([visible], get_texts(item['url_obj'].full))
		converted = replace_breaks(convert_entities(visible_texts))
		stripped = [sent.strip() for sent in sentence_split(converted)]
		item['sentences'] = filters([sentence,length], stripped)
		item['words'] = word_split(stripped)
		self.long_count = item['url_obj'].long_count
		
		return item
	
	def main_parse(self, response):
		item = SiteCrawlerItem()
		item['url_obj'] = URL(response.url, self.scrapeid, self.long_count, parent=self.seed)
		item['social'] = 0
		return self.parse_item(response, item)
	
	def social_parse(self, response):
		#self.log("Bingo! Social page has been parsed!")
		item = SiteCrawlerItem()
		if "facebook" in response.url:
			domain = "facebook.com"
		elif "twitter" in response.url:
			domain = "twitter.com"
		item['url_obj'] = URL(response.url, self.scrapeid, self.long_count, base={'protocol':'http://', 'subdomain':'www.', 'domain':domain, 'path':''})
		item['social'] = 1
		return self.parse_item(response, item)