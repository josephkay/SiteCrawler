from twisted.internet import reactor

from scrapy import log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
#from scrapy.settings import Settings
#from scrapy.utils.project import get_project_settings as Settings
from scrapy.xlib.pydispatch import dispatcher
import logging
import importlib

from SiteCrawler.spiders.sitecrawler_spider import MySpider

from flask import render_template
from initiator import app

def stop_reactor():
    reactor.stop()

@app.route("/runspider/")
def runspider():
	dispatcher.connect(stop_reactor, signal=signals.spider_closed)
	spider = MySpider()
	#crawler = Crawler(Settings())
	
	settings_module = importlib.import_module('SiteCrawler.settings')
	settings = CrawlerSettings(settings_module)
	crawler = Crawler(settings)
	
	crawler.configure()
	crawler.crawl(spider)
	crawler.start()
	log.start(loglevel=logging.DEBUG)
	#log.start()
	log.msg('Running reactor...')
	reactor.run()  # the script will block here until the spider is closed
	log.msg('Reactor stopped.')
	return render_template('stop.html')

