from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from SiteCrawler.items import SiteCrawlerItem
from myfuncs import *

class MySpider(CrawlSpider):
	name = 'SiteCrawler'
	allowed_domains = ['premierinn.com']
	start_urls = ['http://www.premierinn.com']
	
	rules = (
		# Extract links matching 'category.php' (but not matching 'subsection.php')
		# and follow links from them (since no callback means follow=True by default).
		Rule(SgmlLinkExtractor(allow=()), callback='parse_item', follow=True),
	)
	#, process_links='process_links'
	#def process_links(self, links):
		#return [link for link in links if self.valid_links(link)]
	
	#def valid_links(self,link):
		#return link not in self.urls_seen
	
	def parse_item(self, response):
		#self.urls_seen = set()
		self.log('Hi, this is an item page! %s' % response.url)
		
		root = 'http://www.premierinn.com'
		
		hxs = HtmlXPathSelector(response)
		item = SiteCrawlerItem()
		item['url'] = response.url
		item['name'] = url_end(item['url'])
		item['screenshot'] = item['name']+'.png'
		item['links'] = []
		
		for url in hxs.select('//a/@href').extract():
			fixed = url_fix(root, url)
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