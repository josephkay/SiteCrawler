# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class SiteCrawlerItem(Item):
	url_obj = Field()
	links = Field()
	depth = Field()
	social = Field()
	sentences = Field()
	words = Field()