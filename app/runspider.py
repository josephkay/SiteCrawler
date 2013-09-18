from twisted.internet import reactor
from scrapy import log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
from scrapy.log import ScrapyFileLogObserver
#from scrapy.settings import Settings
#from scrapy.utils.project import get_project_settings as Settings
from scrapy.xlib.pydispatch import dispatcher
import logging
import importlib
from SiteCrawler.spiders.sitecrawler_spider import MySpider
from flask import render_template, request, redirect
from initiator import app
import os
import datetime
import calendar

def stop_reactor():
    reactor.stop()

@app.route("/runspider/")
def runspider():
	date = datetime.datetime.utcnow()
	unix_date = calendar.timegm(date.utctimetuple())
	
	route = request.args.get('route')
	domain = request.args.get('domain')
	
	directory = r"{0}\scrapes\{1}\{2}".format(os.getcwd(), domain, unix_date)
	
	if not os.path.exists(directory):
		os.makedirs(directory)
	
	logfile = open('testlog.log', 'w')
	log_observer = ScrapyFileLogObserver(logfile, level=logging.DEBUG)
	log_observer.start()
	log.start(loglevel=logging.DEBUG)
	
	dispatcher.connect(stop_reactor, signal=signals.spider_closed)
	
	spider = MySpider(route, unix_date)
	
	settings_module = importlib.import_module('SiteCrawler.settings')
	settings = CrawlerSettings(settings_module)
	crawler = Crawler(settings)
	
	crawler.configure()
	crawler.crawl(spider)
	crawler.start()
	
	log.msg('Running reactor...')
	reactor.run()  # the script will block here until the spider is closed
	log.msg('Reactor stopped.')
	return redirect(url_for('choose_graph', domain = domain, date = date))

