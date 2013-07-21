# Scrapy settings for SiteCrawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'SiteCrawler'

SPIDER_MODULES = ['SiteCrawler.spiders']
NEWSPIDER_MODULE = 'SiteCrawler.spiders'

ITEM_PIPELINES = [
    'SiteCrawler.pipelines.DuplicatesPipeline',
	'SiteCrawler.pipelines.ScreenshotPipeline',
	'SiteCrawler.pipelines.CsvExportPipeline'
]

DEPTH_LIMIT = 0

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'SiteCrawler (+http://www.yourdomain.com)'
