import sys
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4 import QtCore
from scrapy import log
from spiders.myfuncs import *

class Screenshooter(QWebView):
	def __init__(self):
		log.msg("screenshooter init")
		self.app = QApplication(sys.argv)
		log.msg("screenshooter init complete")

	def capture(self, url, output_path):
		log.msg("screenshooter capture")
		QWebView.__init__(self)
		log.msg("screenshooter capture 1")
		self._loaded = False
		log.msg("screenshooter capture 2")
		self.loadFinished.connect(self._loadFinished)
		log.msg("screenshooter capture 3")
		self.load(QUrl(url))
		log.msg("screenshooter capture 4")
		if "facebook" in url:
			log.msg("screenshooter capture 4.1a")
			delay = 1
		else:
			log.msg("screenshooter capture 4.1b")
			delay = 0
		log.msg("screenshooter capture 4.2")
		self.wait_load(delay=delay)
		log.msg("QUrl loaded")
		# set to webpage size
		frame = self.page().mainFrame()
		log.msg("screenshooter capture 5")
		csize = frame.contentsSize()
		csize.setHeight(csize.height() + 50)
		csize.setWidth(csize.width() + 100)
		self.page().setViewportSize(csize)
		log.msg("screenshooter capture 6")
		# render image
		image = QImage(self.page().viewportSize(), QImage.Format_ARGB32)
		log.msg("screenshooter capture 7")
		painter = QPainter(image)
		log.msg("screenshooter capture 8")
		frame.render(painter)
		log.msg("screenshooter capture 9")
		painter.end()
		log.msg("Saving: {0}".format(output_path))
		try:
			image.save(output_path)
			#crop_image(output_path)
		except Exception, e:
			log.msg("Screenshot saving failed: {0}".format(e))

	def wait_load(self, delay=0):
		# process app events until page loaded
		log.msg("screenshooter capture 4.3")
		while not self._loaded:
			log.msg("screenshooter capture 4.4")
			self.app.processEvents()
			log.msg("screenshooter capture 4.5")
			time.sleep(delay)
			log.msg("screenshooter capture 4.6")
		self._loaded = False
		log.msg("screenshooter capture 4.7")

	def _loadFinished(self, result):
		self._loaded = True

# Use it like this:
#s = Screenshooter()
#s.capture('http://www.premierinn.com', 'website.png')
