from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from SiteCrawler.items import SiteCrawlerItem
from myfuncs import *

class MySpider(CrawlSpider):
	name = 'SiteCrawler'
	rules = (
		Rule(SgmlLinkExtractor(allow=()), callback='parse_item', follow=True),
	)
	
	def __init__(self, root, **kwargs):
		#super(MySpider, self).__init__(*args, **kwargs)
		CrawlSpider.__init__(self, **kwargs)
		self.root = root
		self.start_urls = ['http://' + root]
		self.allowed_domains = [strip_www(root)]
	
	def parse_item(self, response):
		#self.urls_seen = set()
		self.log('Hi, this is an item page! %s' % response.url)
		
		full_root = 'http://' + self.root
		
		hxs = HtmlXPathSelector(response)
		item = SiteCrawlerItem()
		item['url'] = response.url
		item['name'] = get_name(item['url'], strip_www(self.root))
		item['screenshot'] = item['name']+'.png'
		item['links'] = []
		
		for url in hxs.select('//a/@href').extract():
			fixed = url_fix(full_root, url)
			if fixed:
				item['links'].append(fixed)
				#self.urls_seen.add(url)
		return item
		
#		try:
#			depth = response.meta['depth'] + 1
#		except:
#			depth = 0
#		
#		if depth < 5:
#			for url in hxs.select('//a/@href').extract():
#				url = url_fix(root, url)
#				if url:
#					print "URL:  " + url
#					request = Request(url_fix(root, url),callback=self.parse)
#					request.meta['depth'] = depth
#					yield request