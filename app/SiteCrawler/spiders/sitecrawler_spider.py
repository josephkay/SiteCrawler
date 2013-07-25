from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from SiteCrawler.items import SiteCrawlerItem
from myfuncs import *
from myclasses import *

class MySpider(CrawlSpider):
	name = 'SiteCrawler'
	rules = (
		Rule(SgmlLinkExtractor(allow=()), callback='parse_item', follow=True),
	)
	
	def __init__(self, root, **kwargs):
		#super(MySpider, self).__init__(*args, **kwargs)
		CrawlSpider.__init__(self, **kwargs)
		domain = get_domain(root)
		self.seed = URL(root,base={'protocol':'http://', 'subdomain':'', 'domain':domain, 'path':''})
		#self.root = root
		self.start_urls = [self.seed.full]
		self.allowed_domains = [domain]
	
	def parse_item(self, response):
		#self.urls_seen = set()
		#self.log('Hi, this is an item page! %s' % response.url)
		self.log("DEPTH = %i" % response.meta['depth'])
		
		hxs = HtmlXPathSelector(response)
		item = SiteCrawlerItem()
		item['url_obj'] = URL(response.url, parent=self.seed)
		item['url'] = item['url_obj'].full
		item['name'] = item['url_obj'].name
		item['screenshot'] = item['name']+'.png'
		item['depth'] = response.meta['depth']
		item['links'] = []
		
		for url in hxs.select('//a/@href').extract():
			u = URL(url, parent=item['url_obj'])
			if u.domain:
				item['links'].append(u)
		return item