# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class SiteCrawlerItem(Item):
	# define the fields for your item here like:
	# name = Field()
	name = Field()
	url_obj = Field()
	url = Field()
	screenshot = Field()
	links = Field()
	depth = Field()
	path = Field()
	parents = Field()
