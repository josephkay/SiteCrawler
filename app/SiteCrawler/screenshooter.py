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
		self.app = QApplication(sys.argv)

	def capture(self, url, output_path):
		QWebView.__init__(self)
		self._loaded = False
		self.loadFinished.connect(self._loadFinished)
		self.load(QUrl(url))
		if "facebook" in url:
			delay = 1
		else:
			delay = 0
		self.wait_load(delay=delay)
		log.msg("QUrl loaded")
		# set to webpage size
		frame = self.page().mainFrame()
		csize = frame.contentsSize()
		csize.setHeight(csize.height() + 50)
		csize.setWidth(csize.width() + 100)
		self.page().setViewportSize(csize)
		# render image
		image = QImage(self.page().viewportSize(), QImage.Format_ARGB32)
		painter = QPainter(image)
		frame.render(painter)
		painter.end()
		log.msg("Saving: {0}".format(output_path))
		try:
			image.save(output_path)
			#crop_image(output_path)
		except Exception, e:
			log.msg("Screenshot saving failed: {0}".format(e))

	def wait_load(self, delay=0):
		# process app events until page loaded
		while not self._loaded:
			self.app.processEvents()
			time.sleep(delay)
		self._loaded = False

	def _loadFinished(self, result):
		self._loaded = True

# Use it like this:
#s = Screenshooter()
#s.capture('http://www.premierinn.com', 'website.png')
