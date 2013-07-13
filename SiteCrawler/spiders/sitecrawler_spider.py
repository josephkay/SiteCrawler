from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from SiteCrawler.items import SiteCrawlerItem
from screenshooter import Screenshooter
from myfuncs import *

class MySpider(CrawlSpider):
	name = 'sitecrawler'
	allowed_domains = ['premierinn.com']
	start_urls = ['http://www.premierinn.com']
	
	def parse(self, response):
		self.log('Hi, this is an item page! %s' % response.url)
		
		hxs = HtmlXPathSelector(response)
		item = SiteCrawlerItem()
		item['url'] = response.url
		item['name'] = url_end(item['url'])
		
		s = Screenshooter()
		image = item['name']+'.png'
		s.capture(item['url'], image)
		item['screenshot'] = image
		
		print item
		return item